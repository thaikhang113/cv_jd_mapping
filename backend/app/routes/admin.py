from fastapi import APIRouter, Depends
from app.database import db
from app.dependencies import require_roles, serialize_doc

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_roles("admin"))])

@router.get("/stats")
async def stats():
    return {name: await db[name].count_documents({}) for name in ["users", "cvs", "jobs", "matching_results", "applications", "conversations", "messages"]}

@router.get("/users")
async def users(): return [serialize_doc(x) async for x in db.users.find({}, {"password_hash": 0})]
@router.get("/cvs")
async def cvs(): return [serialize_doc(x) async for x in db.cvs.find({})]
@router.get("/jobs")
async def jobs(): return [serialize_doc(x) async for x in db.jobs.find({})]
@router.get("/matches")
async def matches(): return [serialize_doc(x) async for x in db.matching_results.find({})]
@router.get("/applications")
async def applications(): return [serialize_doc(x) async for x in db.applications.find({})]
