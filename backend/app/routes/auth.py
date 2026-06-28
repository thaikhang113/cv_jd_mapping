from fastapi import APIRouter, HTTPException, Depends
from app.database import db
from app.dependencies import hash_password, verify_password, create_access_token, now_utc, serialize_doc, get_current_user, ROLES
from app.schemas.common import RegisterIn, LoginIn, TokenOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
async def register(payload: RegisterIn):
    if payload.role not in ROLES - {"admin"}:
        raise HTTPException(400, "Invalid role")
    existing = await db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(409, "Email already registered")
    doc = {"name": payload.name, "email": payload.email.lower(), "password_hash": hash_password(payload.password), "role": payload.role, "is_blocked": False, "created_at": now_utc(), "updated_at": now_utc()}
    result = await db.users.insert_one(doc)
    user = serialize_doc(await db.users.find_one({"_id": result.inserted_id}))
    return {"access_token": create_access_token({"sub": user["id"], "role": user["role"]}), "user": user}

@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn):
    user_doc = await db.users.find_one({"email": payload.email.lower()})
    if not user_doc or not verify_password(payload.password, user_doc["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    if user_doc.get("is_blocked"):
        raise HTTPException(403, "User blocked")
    user = serialize_doc(user_doc)
    return {"access_token": create_access_token({"sub": user["id"], "role": user["role"]}), "user": user}

@router.get("/me")
async def me(user=Depends(get_current_user)):
    return user
