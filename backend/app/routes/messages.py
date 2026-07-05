from fastapi import APIRouter, Depends, HTTPException
from app.database import db
from app.dependencies import get_current_user, oid, serialize_doc, now_utc
from app.schemas.common import ConversationIn, MessageIn

router = APIRouter(tags=["messages"])

async def enrich_conversation(convo, user_id):
    doc = serialize_doc(convo)
    current = oid(user_id)
    other_id = next((pid for pid in convo.get("participant_ids", []) if pid != current), None)
    other = await db.users.find_one({"_id": other_id}, {"password_hash": 0}) if other_id else None
    last = await db.messages.find_one({"conversation_id": convo["_id"]}, sort=[("created_at", -1)])
    doc["other_id"] = str(other_id) if other_id else None
    doc["other_name"] = other.get("name") if other else "User"
    doc["last_message"] = last.get("content") if last else "No messages"
    return doc

async def enrich_messages(rows, user_id):
    sender_ids = list({row["sender_id"] for row in rows})
    users = {u["_id"]: u async for u in db.users.find({"_id": {"$in": sender_ids}}, {"password_hash": 0})} if sender_ids else {}
    current = oid(user_id)
    enriched = []
    for row in rows:
        doc = serialize_doc(row)
        sender = users.get(row["sender_id"], {})
        doc["sender_name"] = sender.get("name", "User")
        doc["is_me"] = row["sender_id"] == current
        enriched.append(doc)
    return enriched

@router.post("/api/conversations")
async def create_conversation(payload: ConversationIn, user=Depends(get_current_user)):
    other = await db.users.find_one({"_id": oid(payload.participant_id)})
    if not other:
        raise HTTPException(404, "Participant not found")
    participants = sorted([oid(user["id"]), oid(payload.participant_id)], key=str)
    doc = {"participant_ids": participants, "job_id": oid(payload.job_id) if payload.job_id else None, "created_at": now_utc(), "updated_at": now_utc()}
    existing = await db.conversations.find_one({"participant_ids": participants, "job_id": doc["job_id"]})
    if existing:
        return await enrich_conversation(existing, user["id"])
    result = await db.conversations.insert_one(doc)
    return await enrich_conversation(await db.conversations.find_one({"_id": result.inserted_id}), user["id"])

@router.get("/api/conversations/my")
async def my_conversations(user=Depends(get_current_user)):
    rows = [c async for c in db.conversations.find({"participant_ids": oid(user["id"])}).sort("updated_at", -1)]
    return [await enrich_conversation(c, user["id"]) for c in rows]

@router.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user=Depends(get_current_user)):
    convo = await db.conversations.find_one({"_id": oid(conversation_id), "participant_ids": oid(user["id"])})
    if not convo:
        raise HTTPException(404, "Conversation not found")
    return await enrich_conversation(convo, user["id"])

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
    rows = [m async for m in db.messages.find({"conversation_id": convo["_id"]}).sort("created_at", 1)]
    return await enrich_messages(rows, user["id"])

@router.put("/api/messages/{message_id}/read")
async def mark_read(message_id: str, user=Depends(get_current_user)):
    await db.messages.update_one({"_id": oid(message_id)}, {"$addToSet": {"read_by": oid(user["id"])}})
    return {"ok": True}
