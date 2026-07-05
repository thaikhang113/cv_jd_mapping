from fastapi import APIRouter, Depends, HTTPException
from app.database import db
from app.dependencies import get_current_user, require_roles, oid, serialize_doc, now_utc

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me")
async def profile(user=Depends(get_current_user)):
    return user

@router.put("/me")
async def update_profile(payload: dict, user=Depends(get_current_user)):
    updates = {"updated_at": now_utc()}
    if "name" in payload:
        name = str(payload.get("name", "")).strip()
        if len(name) < 2:
            raise HTTPException(400, "Name must be at least 2 characters")
        updates["name"] = name
    if "primary_cv_id" in payload:
        cv_id = oid(payload["primary_cv_id"])
        cv = await db.cvs.find_one({"_id": cv_id, "owner_id": oid(user["id"]), "processing_status": "done"})
        if not cv:
            raise HTTPException(400, "Processed CV not found")
        updates["primary_cv_id"] = cv_id
    if len(updates) == 1:
        raise HTTPException(400, "Nothing to update")
    await db.users.update_one({"_id": oid(user["id"])}, {"$set": updates})
    return serialize_doc(await db.users.find_one({"_id": oid(user["id"])}, {"password_hash": 0}))

@router.get("")
async def users(_: dict = Depends(require_roles("admin"))):
    return [serialize_doc(u) async for u in db.users.find({}, {"password_hash": 0})]

@router.put("/{user_id}/block")
async def block_user(user_id: str, payload: dict, _: dict = Depends(require_roles("admin"))):
    await db.users.update_one({"_id": oid(user_id)}, {"$set": {"is_blocked": bool(payload.get("is_blocked")), "updated_at": now_utc()}})
    return {"ok": True}
