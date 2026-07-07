from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from app.config import settings
from app.database import db
from app.dependencies import get_current_user, require_roles, oid, serialize_doc, now_utc
from app.services.cv_parser import extract_text, parse_cv_text
from app.services.cv_worker import enqueue_cv

router = APIRouter(prefix="/api/cvs", tags=["cvs"])

def limit_label(size):
    if size % (1024 * 1024) == 0:
        return f"{size // (1024 * 1024)} MB"
    return f"{size} bytes"

async def save_cv(file: UploadFile, user: dict):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(400, "Only PDF/DOCX supported")
    upload_dir = Path(settings.upload_dir).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid4().hex}{suffix}"
    path = upload_dir / safe_name
    max_size = settings.max_cv_file_bytes
    data = await file.read(max_size + 1)
    if len(data) > max_size:
        raise HTTPException(413, f"File exceeds {limit_label(max_size)} limit")
    path.write_bytes(data)
    created_at = now_utc()
    raw_text = ""
    extracted_data = {}
    processing_status = "done"
    processing_error = None
    try:
        raw_text = extract_text(str(path))
        extracted_data = parse_cv_text(raw_text)
    except Exception as exc:
        processing_status = "failed"
        processing_error = str(exc)
    doc = {
        "owner_id": oid(user["id"]),
        "uploaded_by_role": user["role"],
        "filename": file.filename,
        "file_path": str(path),
        "raw_text": raw_text,
        "extracted_data": extracted_data,
        "processing_status": processing_status,
        "created_at": created_at,
        "updated_at": created_at,
    }
    if processing_error:
        doc["processing_error"] = processing_error
    result = await db.cvs.insert_one(doc)
    if user["role"] == "candidate" and processing_status == "done":
        await db.users.update_one({"_id": oid(user["id"])}, {"$set": {"primary_cv_id": result.inserted_id, "updated_at": now_utc()}})
    if processing_status == "done":
        await enqueue_cv(result.inserted_id, oid(user["id"]), mark_queued=False)
    cv = serialize_doc(await db.cvs.find_one({"_id": result.inserted_id}))
    cv["queued"] = processing_status == "done"
    return cv
@router.post("/upload")
async def upload_cv(file: UploadFile = File(...), user=Depends(require_roles("candidate", "recruiter", "admin"))):
    return await save_cv(file, user)

@router.post("/upload-multiple")
async def upload_multiple(files: list[UploadFile] = File(...), user=Depends(require_roles("recruiter", "admin"))):
    return [await save_cv(file, user) for file in files]

@router.get("/my")
async def my_cvs(user=Depends(get_current_user)):
    primary = str(user.get("primary_cv_id") or "")
    rows = []
    async for cv in db.cvs.find({"owner_id": oid(user["id"])}).sort("updated_at", -1):
        doc = serialize_doc(cv)
        doc["is_primary"] = doc["id"] == primary
        rows.append(doc)
    return rows

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
