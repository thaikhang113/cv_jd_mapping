from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError
from app.database import db
from app.dependencies import get_current_user, require_roles, oid, serialize_doc, now_utc
from app.schemas.common import ApplicationIn, StatusIn

STATUSES = {"applied","shortlisted","interviewing","offered","rejected","hired"}
router = APIRouter(prefix="/api/applications", tags=["applications"])

async def enrich_applications(rows):
    job_ids = list({row["job_id"] for row in rows})
    user_ids = list({row["candidate_id"] for row in rows} | {row["recruiter_id"] for row in rows})
    jobs = {job["_id"]: job async for job in db.jobs.find({"_id": {"$in": job_ids}})} if job_ids else {}
    users = {u["_id"]: u async for u in db.users.find({"_id": {"$in": user_ids}}, {"password_hash": 0})} if user_ids else {}
    enriched = []
    for row in rows:
        doc = serialize_doc(row)
        job = jobs.get(row["job_id"], {})
        candidate = users.get(row["candidate_id"], {})
        recruiter = users.get(row["recruiter_id"], {})
        doc.update({
            "job_title": job.get("title", doc["job_id"]),
            "company_name": job.get("company_name", ""),
            "candidate_name": candidate.get("name", doc["candidate_id"]),
            "recruiter_name": recruiter.get("name", doc["recruiter_id"]),
        })
        enriched.append(doc)
    return enriched

@router.post("")
async def apply(payload: ApplicationIn, user=Depends(require_roles("candidate"))):
    job = await db.jobs.find_one({"_id": oid(payload.job_id), "status": "open"})
    if not job:
        raise HTTPException(404, "Open job not found")
    cv_id = oid(payload.cv_id) if payload.cv_id else None
    if cv_id:
        cv = await db.cvs.find_one({"_id": cv_id, "owner_id": oid(user["id"]), "processing_status": "done"})
        if not cv:
            raise HTTPException(400, "Processed CV not found")
    else:
        primary_cv_id = user.get("primary_cv_id")
        cv = None
        if primary_cv_id:
            cv = await db.cvs.find_one({"_id": oid(primary_cv_id), "owner_id": oid(user["id"]), "processing_status": "done"})
        if not cv:
            cv = await db.cvs.find_one({"owner_id": oid(user["id"]), "processing_status": "done"}, sort=[("updated_at", -1)])
        if not cv:
            raise HTTPException(400, "Select a primary CV before applying")
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
    rows = [a async for a in db.applications.find(query)]
    return await enrich_applications(rows)

@router.get("/job/{job_id}")
async def job_apps(job_id: str, user=Depends(require_roles("recruiter", "admin"))):
    query = {"job_id": oid(job_id)}
    if user["role"] == "recruiter":
        query["recruiter_id"] = oid(user["id"])
    rows = [a async for a in db.applications.find(query)]
    return await enrich_applications(rows)

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
