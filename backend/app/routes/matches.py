from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from app.database import db
from app.dependencies import get_current_user, require_roles, oid, serialize_doc, now_utc
from app.services.matching import compute_match

router = APIRouter(prefix="/api/matches", tags=["matches"])


def attach_cv_info(row: dict, cv: dict) -> dict:
    data = cv.get("extracted_data", {}) if cv else {}
    row.update({
        "cv_filename": cv.get("filename", "") if cv else "",
        "cv_name": data.get("name"),
        "candidate_name": data.get("name"),
        "cv_email": data.get("email"),
        "cv_phone": data.get("phone"),
        "cv_skills": data.get("skills", []),
        "cv_experience_years": data.get("experience_years", 0),
    })
    return row


async def count_cvs(query: dict) -> int:
    if hasattr(db.cvs, "count_documents"):
        return await db.cvs.count_documents(query)
    count = 0
    async for _ in db.cvs.find(query):
        count += 1
    return count

@router.post("/run")
async def run_matches(payload: dict, user=Depends(require_roles("recruiter", "admin")), background_tasks: BackgroundTasks = None):
    job_id = payload.get("job_id")
    job = await db.jobs.find_one({"_id": oid(job_id)})
    if not job:
        raise HTTPException(404, "Job not found")
    if user["role"] != "admin" and str(job["recruiter_id"]) != user["id"]:
        raise HTTPException(403, "Forbidden")
    total = await count_cvs({"processing_status": "done"})
    now = now_utc()
    result = await db.match_runs.insert_one({
        "job_id": job["_id"],
        "recruiter_id": job["recruiter_id"],
        "status": "queued",
        "total": total,
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "created_at": now,
        "updated_at": now,
    })
    run_id = result.inserted_id
    if background_tasks:
        background_tasks.add_task(process_match_run, run_id)
    return {"run_id": str(run_id), "job_id": str(job["_id"]), "total": total, "processed": 0, "succeeded": 0, "failed": 0, "percent": 0, "status": "queued"}


async def process_match_run(run_id: ObjectId):
    run = await db.match_runs.find_one({"_id": run_id})
    if not run:
        return
    job = await db.jobs.find_one({"_id": run["job_id"]})
    if not job:
        await db.match_runs.update_one({"_id": run_id}, {"$set": {"status": "failed", "error": "Job not found", "updated_at": now_utc()}})
        return
    await db.match_runs.update_one({"_id": run_id}, {"$set": {"status": "running", "updated_at": now_utc()}})
    query = {"processing_status": "done"}
    rows = []
    async for cv in db.cvs.find(query):
        try:
            result = compute_match(cv, job)
            result.update({"job_id": job["_id"], "cv_id": cv["_id"], "recruiter_id": job["recruiter_id"], "created_at": now_utc(), "updated_at": now_utc()})
            attach_cv_info(result, cv)
            await db.matching_results.update_one({"job_id": job["_id"], "cv_id": cv["_id"]}, {"$set": result}, upsert=True)
            rows.append(result)
            await db.match_runs.update_one({"_id": run_id}, {"$inc": {"processed": 1, "succeeded": 1}, "$set": {"updated_at": now_utc()}})
        except Exception as exc:
            await db.match_runs.update_one({"_id": run_id}, {"$inc": {"processed": 1, "failed": 1}, "$set": {"last_error": str(exc), "updated_at": now_utc()}})
    rows.sort(key=lambda r: r["overall_score"], reverse=True)
    for index, row in enumerate(rows, 1):
        await db.matching_results.update_one({"job_id": row["job_id"], "cv_id": row["cv_id"]}, {"$set": {"rank": index}})
        row["rank"] = index
    await db.match_runs.update_one({"_id": run_id}, {"$set": {"status": "done", "updated_at": now_utc()}})


@router.get("/run/{run_id}")
async def match_run_status(run_id: str, user=Depends(get_current_user)):
    run = await db.match_runs.find_one({"_id": oid(run_id)})
    if not run:
        raise HTTPException(404, "Run not found")
    if user["role"] != "admin" and str(run["recruiter_id"]) != user["id"]:
        raise HTTPException(403, "Forbidden")
    payload = serialize_doc(run)
    total = payload.get("total") or 0
    processed = payload.get("processed") or 0
    payload["percent"] = round((processed / total) * 100) if total else 100
    if payload.get("status") == "done":
        rows = [r async for r in db.matching_results.find({"job_id": run["job_id"]}).sort("overall_score", -1)]
        payload["results"] = [serialize_doc(r) for r in rows]
    return payload

@router.get("/job/{job_id}")
async def job_matches(job_id: str, user=Depends(get_current_user)):
    rows = [r async for r in db.matching_results.find({"job_id": oid(job_id)}).sort("overall_score", -1)]
    missing_cv_ids = [r["cv_id"] for r in rows if not r.get("cv_email")]
    cvs = {cv["_id"]: cv async for cv in db.cvs.find({"_id": {"$in": missing_cv_ids}})} if missing_cv_ids else {}
    return [serialize_doc(attach_cv_info(r, cvs.get(r["cv_id"], {})) if r["cv_id"] in cvs else r) for r in rows]

@router.get("/my")
async def my_matches(user=Depends(get_current_user)):
    if user["role"] == "candidate":
        cv_ids = [cv["_id"] async for cv in db.cvs.find({"owner_id": oid(user["id"])}, {"_id": 1})]
        if not cv_ids:
            return []
        query = {"cv_id": {"$in": cv_ids}}
    elif user["role"] == "recruiter":
        query = {"recruiter_id": oid(user["id"])}
    else:
        query = {}
    rows = [r async for r in db.matching_results.find(query).sort("overall_score", -1)]
    missing_cv_ids = [r["cv_id"] for r in rows if not r.get("cv_email")]
    cvs = {cv["_id"]: cv async for cv in db.cvs.find({"_id": {"$in": missing_cv_ids}})} if missing_cv_ids else {}
    return [serialize_doc(attach_cv_info(r, cvs.get(r["cv_id"], {})) if r["cv_id"] in cvs else r) for r in rows]
