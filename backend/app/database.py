from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.database_name]

async def ping_db():
    return await client.admin.command("ping")

async def ensure_indexes():
    await db.users.create_index("email", unique=True)
    await db.cvs.create_index("owner_id")
    await db.jobs.create_index("recruiter_id")
    await db.matching_results.create_index([("job_id", 1), ("cv_id", 1)], unique=True)
    await db.applications.create_index([("job_id", 1), ("candidate_id", 1)], unique=True)
    await db.conversations.create_index("participant_ids")
