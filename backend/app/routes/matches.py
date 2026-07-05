from fastapi import APIRouter, Depends, HTTPException
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

@router.post("/run")
async def run_matches(payload: dict, user=Depends(require_roles("recruiter", "admin"))):
    job_id = payload.get("job_id")
    job = await db.jobs.find_one({"_id": oid(job_id)})
    if not job:
        raise HTTPException(404, "Job not found")
    if user["role"] != "admin" and str(job["recruiter_id"]) != user["id"]:
        raise HTTPException(403, "Forbidden")
    query = {"processing_status": "done"}
    rows = []
    async for cv in db.cvs.find(query):
        result = compute_match(cv, job)
        result.update({"job_id": job["_id"], "cv_id": cv["_id"], "recruiter_id": job["recruiter_id"], "created_at": now_utc(), "updated_at": now_utc()})
        attach_cv_info(result, cv)
        await db.matching_results.update_one({"job_id": job["_id"], "cv_id": cv["_id"]}, {"$set": result}, upsert=True)
        rows.append(result)
    rows.sort(key=lambda r: r["overall_score"], reverse=True)
    for index, row in enumerate(rows, 1):
        await db.matching_results.update_one({"job_id": row["job_id"], "cv_id": row["cv_id"]}, {"$set": {"rank": index}})
        row["rank"] = index
    return [serialize_doc(r) for r in rows]

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
