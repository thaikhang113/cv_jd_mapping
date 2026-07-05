from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from app.config import settings
from app.database import db
from app.dependencies import require_roles, oid, serialize_doc, now_utc
from app.schemas.common import JobIn
from app.services.jd_parser import parse_jd_text, extract_text

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


async def remember_taxonomy(user, job):
    now = now_utc()
    owner = oid(user["id"])
    for term in set((job.get("required_skills") or []) + (job.get("nice_to_have_skills") or [])):
        await db.taxonomy_terms.update_one(
            {"owner_id": owner, "term": term.lower(), "type": "skill"},
            {"$set": {"label": term, "scope": "recruiter", "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
    if job.get("category"):
        await db.taxonomy_terms.update_one(
            {"owner_id": owner, "term": job["category"].lower(), "type": "category"},
            {"$set": {"label": job["category"], "scope": "recruiter", "updated_at": now}, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )


@router.post("/parse-document")
async def parse_job_document(file: UploadFile = File(...), user=Depends(require_roles("recruiter", "admin"))):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(400, "Only PDF/DOCX supported")
    upload_dir = Path(settings.upload_dir) / "jds"
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{uuid4().hex}{suffix}"
    path.write_bytes(await file.read())
    raw_text = extract_text(str(path))
    draft = parse_jd_text(raw_text)
    doc = {
        "owner_id": oid(user["id"]),
        "filename": file.filename,
        "file_path": str(path),
        "raw_text": raw_text,
        "draft": draft,
        "status": "done",
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
    result = await db.document_parse_logs.insert_one(doc)
    return {"parse_id": str(result.inserted_id), "filename": file.filename, "draft": draft}


@router.post("")
async def create_job(payload: JobIn, user=Depends(require_roles("recruiter", "admin"))):
    doc = payload.model_dump()
    doc.update({"recruiter_id": oid(user["id"]), "created_at": now_utc(), "updated_at": now_utc()})
    result = await db.jobs.insert_one(doc)
    await remember_taxonomy(user, doc)
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
    await remember_taxonomy(user, data)
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
