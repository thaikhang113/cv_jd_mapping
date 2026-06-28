from fastapi import APIRouter, Depends, HTTPException
from app.database import db
from app.dependencies import get_current_user, oid, serialize_doc, now_utc
from app.schemas.common import ConversationIn, MessageIn

router = APIRouter(tags=["messages"])

@router.post("/api/conversations")
async def create_conversation(payload: ConversationIn, user=Depends(get_current_user)):
    other = await db.users.find_one({"_id": oid(payload.participant_id)})
    if not other:
        raise HTTPException(404, "Participant not found")
    participants = sorted([oid(user["id"]), oid(payload.participant_id)], key=str)
    doc = {"participant_ids": participants, "job_id": oid(payload.job_id) if payload.job_id else None, "created_at": now_utc(), "updated_at": now_utc()}
    existing = await db.conversations.find_one({"participant_ids": participants, "job_id": doc["job_id"]})
    if existing:
        return serialize_doc(existing)
    result = await db.conversations.insert_one(doc)
    return serialize_doc(await db.conversations.find_one({"_id": result.inserted_id}))

@router.get("/api/conversations/my")
async def my_conversations(user=Depends(get_current_user)):
    return [serialize_doc(c) async for c in db.conversations.find({"participant_ids": oid(user["id"])})]

@router.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user=Depends(get_current_user)):
    convo = await db.conversations.find_one({"_id": oid(conversation_id), "participant_ids": oid(user["id"])})
    if not convo:
        raise HTTPException(404, "Conversation not found")
    return serialize_doc(convo)

@router.post("/api/messages")
async def send_message(payload: MessageIn, user=Depends(get_current_user)):
    convo = await db.conversations.find_one({"_id": oid(payload.conversation_id), "participant_ids": oid(user["id"])})
    if not convo:
        raise HTTPException(404, "Conversation not found")
    doc = {"conversation_id": convo["_id"], "sender_id": oid(user["id"]), "content": payload.content, "read_by": [oid(user["id"])], "created_at": now_utc(), "updated_at": now_utc()}
    result = await db.messages.insert_one(doc)
    await db.conversations.update_one({"_id": convo["_id"]}, {"$set": {"updated_at": now_utc()}})
    return serialize_doc(await db.messages.find_one({"_id": result.inserted_id}))

@router.get("/api/messages/{conversation_id}")
async def list_messages(conversation_id: str, user=Depends(get_current_user)):
    convo = await db.conversations.find_one({"_id": oid(conversation_id), "participant_ids": oid(user["id"])})
    if not convo:
        raise HTTPException(404, "Conversation not found")
    return [serialize_doc(m) async for m in db.messages.find({"conversation_id": convo["_id"]}).sort("created_at", 1)]

@router.put("/api/messages/{message_id}/read")
async def mark_read(message_id: str, user=Depends(get_current_user)):
    await db.messages.update_one({"_id": oid(message_id)}, {"$addToSet": {"read_by": oid(user["id"])}})
    return {"ok": True}
