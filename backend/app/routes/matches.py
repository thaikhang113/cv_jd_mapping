from fastapi import APIRouter, Depends, HTTPException
from app.database import db
from app.dependencies import get_current_user, require_roles, oid, serialize_doc, now_utc
from app.services.matching import compute_match

router = APIRouter(prefix="/api/matches", tags=["matches"])

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
        await db.matching_results.update_one({"job_id": job["_id"], "cv_id": cv["_id"]}, {"$set": result}, upsert=True)
        rows.append(result)
    rows.sort(key=lambda r: r["overall_score"], reverse=True)
    for index, row in enumerate(rows, 1):
        await db.matching_results.update_one({"job_id": row["job_id"], "cv_id": row["cv_id"]}, {"$set": {"rank": index}})
        row["rank"] = index
    return [serialize_doc(r) for r in rows]

@router.get("/job/{job_id}")
async def job_matches(job_id: str, user=Depends(get_current_user)):
    rows = [serialize_doc(r) async for r in db.matching_results.find({"job_id": oid(job_id)}).sort("rank", 1)]
    return rows

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
    return [serialize_doc(r) async for r in db.matching_results.find(query).sort("overall_score", -1)]
