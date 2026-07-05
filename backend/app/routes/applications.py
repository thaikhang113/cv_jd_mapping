from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from app.database import db
from app.dependencies import get_current_user, require_roles, oid, serialize_doc, now_utc
from app.schemas.common import ApplicationIn, StatusIn

STATUSES = {"applied","shortlisted","interviewing","offered","rejected","hired"}
router = APIRouter(prefix="/api/applications", tags=["applications"])

@router.post("")
async def apply(payload: ApplicationIn, user=Depends(require_roles("candidate"))):
    job = await db.jobs.find_one({"_id": oid(payload.job_id), "status": "open"})
    if not job:
        raise HTTPException(404, "Open job not found")
    cv_id = oid(payload.cv_id) if payload.cv_id else None
    if not cv_id:
        cv = await db.cvs.find_one({"owner_id": oid(user["id"])})
        if not cv:
            raise HTTPException(400, "Upload CV first")
        cv_id = cv["_id"]
    doc = {"job_id": job["_id"], "candidate_id": oid(user["id"]), "cv_id": cv_id, "recruiter_id": job["recruiter_id"], "status": "applied", "created_at": now_utc(), "updated_at": now_utc()}
    try:
        result = await db.applications.insert_one(doc)
        return serialize_doc(await db.applications.find_one({"_id": result.inserted_id}))
    except DuplicateKeyError:
        existing = await db.applications.find_one({"job_id": job["_id"], "candidate_id": oid(user["id"])})
        if existing:
            return serialize_doc(existing)
        raise

@router.get("/my")
async def my_apps(user=Depends(get_current_user)):
    query = {"candidate_id": oid(user["id"])} if user["role"] == "candidate" else {"recruiter_id": oid(user["id"])}
    return [serialize_doc(a) async for a in db.applications.find(query)]

@router.get("/job/{job_id}")
async def job_apps(job_id: str, user=Depends(require_roles("recruiter", "admin"))):
    query = {"job_id": oid(job_id)}
    if user["role"] == "recruiter":
        query["recruiter_id"] = oid(user["id"])
    return [serialize_doc(a) async for a in db.applications.find(query)]

@router.put("/{application_id}/status")
async def update_status(application_id: str, payload: StatusIn, user=Depends(require_roles("recruiter", "admin"))):
    if payload.status not in STATUSES:
        raise HTTPException(400, "Invalid status")
    app = await db.applications.find_one({"_id": oid(application_id)})
    if not app:
        raise HTTPException(404, "Application not found")
    if user["role"] == "recruiter" and str(app["recruiter_id"]) != user["id"]:
        raise HTTPException(403, "Forbidden")
    await db.applications.update_one({"_id": oid(application_id)}, {"$set": {"status": payload.status, "updated_at": now_utc()}})
    return serialize_doc(await db.applications.find_one({"_id": oid(application_id)}))
