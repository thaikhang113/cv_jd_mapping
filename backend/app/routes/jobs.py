from fastapi import APIRouter, Depends, HTTPException
from app.database import db
from app.dependencies import get_current_user, require_roles, oid, serialize_doc, now_utc
from app.schemas.common import JobIn

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.post("")
async def create_job(payload: JobIn, user=Depends(require_roles("recruiter", "admin"))):
    doc = payload.model_dump()
    doc.update({"recruiter_id": oid(user["id"]), "created_at": now_utc(), "updated_at": now_utc()})
    result = await db.jobs.insert_one(doc)
    return serialize_doc(await db.jobs.find_one({"_id": result.inserted_id}))

@router.get("")
async def list_jobs():
    return [serialize_doc(j) async for j in db.jobs.find({"status": "open"})]

@router.get("/my")
async def my_jobs(user=Depends(require_roles("recruiter", "admin"))):
    query = {} if user["role"] == "admin" else {"recruiter_id": oid(user["id"])}
    return [serialize_doc(j) async for j in db.jobs.find(query)]

@router.get("/{job_id}")
async def get_job(job_id: str):
    job = await db.jobs.find_one({"_id": oid(job_id)})
    if not job:
        raise HTTPException(404, "Job not found")
    return serialize_doc(job)

@router.put("/{job_id}")
async def update_job(job_id: str, payload: JobIn, user=Depends(require_roles("recruiter", "admin"))):
    job = await db.jobs.find_one({"_id": oid(job_id)})
    if not job:
        raise HTTPException(404, "Job not found")
    if user["role"] != "admin" and str(job["recruiter_id"]) != user["id"]:
        raise HTTPException(403, "Forbidden")
    data = payload.model_dump(); data["updated_at"] = now_utc()
    await db.jobs.update_one({"_id": oid(job_id)}, {"$set": data})
    return serialize_doc(await db.jobs.find_one({"_id": oid(job_id)}))

@router.delete("/{job_id}")
async def delete_job(job_id: str, user=Depends(require_roles("recruiter", "admin"))):
    job = await db.jobs.find_one({"_id": oid(job_id)})
    if not job:
        raise HTTPException(404, "Job not found")
    if user["role"] != "admin" and str(job["recruiter_id"]) != user["id"]:
        raise HTTPException(403, "Forbidden")
    await db.jobs.delete_one({"_id": oid(job_id)})
    return {"ok": True}
