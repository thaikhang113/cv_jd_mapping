from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from app.config import settings
from app.database import db
from app.dependencies import get_current_user, require_roles, oid, serialize_doc, now_utc
from app.services.cv_worker import enqueue_cv

router = APIRouter(prefix="/api/cvs", tags=["cvs"])

async def save_cv(file: UploadFile, user: dict):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(400, "Only PDF/DOCX supported")
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid4().hex}{suffix}"
    path = upload_dir / safe_name
    path.write_bytes(await file.read())
    doc = {
        "owner_id": oid(user["id"]),
        "uploaded_by_role": user["role"],
        "filename": file.filename,
        "file_path": str(path),
        "raw_text": "",
        "extracted_data": {},
        "processing_status": "queued",
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
    result = await db.cvs.insert_one(doc)
    await enqueue_cv(result.inserted_id, oid(user["id"]))
    cv = serialize_doc(await db.cvs.find_one({"_id": result.inserted_id}))
    cv["queued"] = True
    return cv

@router.post("/upload")
async def upload_cv(file: UploadFile = File(...), user=Depends(require_roles("candidate", "recruiter", "admin"))):
    return await save_cv(file, user)

@router.post("/upload-multiple")
async def upload_multiple(files: list[UploadFile] = File(...), user=Depends(require_roles("recruiter", "admin"))):
    return [await save_cv(file, user) for file in files]

@router.get("/my")
async def my_cvs(user=Depends(get_current_user)):
    return [serialize_doc(c) async for c in db.cvs.find({"owner_id": oid(user["id"])})]

@router.get("/{cv_id}")
async def get_cv(cv_id: str, user=Depends(get_current_user)):
    cv = await db.cvs.find_one({"_id": oid(cv_id)})
    if not cv:
        raise HTTPException(404, "CV not found")
    if user["role"] != "admin" and str(cv["owner_id"]) != user["id"]:
        raise HTTPException(403, "Forbidden")
    return serialize_doc(cv)

@router.delete("/{cv_id}")
async def delete_cv(cv_id: str, user=Depends(get_current_user)):
    cv = await db.cvs.find_one({"_id": oid(cv_id)})
    if not cv:
        raise HTTPException(404, "CV not found")
    if user["role"] != "admin" and str(cv["owner_id"]) != user["id"]:
        raise HTTPException(403, "Forbidden")
    await db.cvs.delete_one({"_id": oid(cv_id)})
    return {"ok": True}
