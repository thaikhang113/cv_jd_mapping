from fastapi import APIRouter, Depends, HTTPException
from app.database import db
from app.dependencies import get_current_user, require_roles, oid, serialize_doc, now_utc

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me")
async def profile(user=Depends(get_current_user)):
    return user

@router.get("")
async def users(_: dict = Depends(require_roles("admin"))):
    return [serialize_doc(u) async for u in db.users.find({}, {"password_hash": 0})]

@router.put("/{user_id}/block")
async def block_user(user_id: str, payload: dict, _: dict = Depends(require_roles("admin"))):
    await db.users.update_one({"_id": oid(user_id)}, {"$set": {"is_blocked": bool(payload.get("is_blocked")), "updated_at": now_utc()}})
    return {"ok": True}
