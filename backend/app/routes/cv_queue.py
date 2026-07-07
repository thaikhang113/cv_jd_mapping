from fastapi import APIRouter, Depends, HTTPException
from app.database import db
from app.dependencies import get_current_user, require_roles, oid, serialize_doc
from app.services.cv_worker import claim_queue_item, process_queue_item

router = APIRouter(prefix="/api/cv-queue", tags=["cv-queue"])


def can_view(item: dict, user: dict) -> bool:
    return user["role"] == "admin" or str(item.get("owner_id")) == user["id"]


@router.get("/status/{cv_id}")
async def queue_status(cv_id: str, include_matches: bool = False, user=Depends(get_current_user)):
    item = await db.cv_processing_queue.find_one({"cv_id": oid(cv_id)})
    if not item:
        raise HTTPException(404, "Queue item not found")
    if not can_view(item, user):
        raise HTTPException(403, "Forbidden")
    cv = await db.cvs.find_one({"_id": oid(cv_id)})
    payload = serialize_doc(item)
    payload["cv"] = serialize_doc(cv) if cv else None
    if include_matches:
        payload["matches"] = [serialize_doc(row) async for row in db.matching_results.find({"cv_id": oid(cv_id)}).sort("overall_score", -1)]
    return payload


@router.get("/recent")
async def recent_queue(user=Depends(get_current_user)):
    query = {} if user["role"] == "admin" else {"owner_id": oid(user["id"])}
    return [serialize_doc(item) async for item in db.cv_processing_queue.find(query).sort("created_at", -1).limit(20)]


@router.post("/process-now")
async def process_now(_: dict = Depends(require_roles("admin", "recruiter"))):
    item = await claim_queue_item(0)
    if not item:
        return {"processed": False, "reason": "queue empty"}
    matched_jobs = await process_queue_item(item)
    await db.cv_processing_queue.update_one({"_id": item["_id"]}, {"$set": {"status": "done", "matched_jobs": matched_jobs}})
    return {"processed": True, "cv_id": str(item["cv_id"]), "matched_jobs": matched_jobs}
