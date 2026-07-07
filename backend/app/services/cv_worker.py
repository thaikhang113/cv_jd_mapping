import asyncio
from pymongo import ReturnDocument, UpdateOne
from app.config import settings
from app.database import db
from app.dependencies import now_utc
from app.services.cv_parser import extract_text, parse_cv_text
from app.services.matching import compute_match


async def enqueue_cv(cv_id, owner_id, mark_queued: bool = True):
    now = now_utc()
    doc = {
        "cv_id": cv_id,
        "owner_id": owner_id,
        "status": "pending",
        "attempts": 0,
        "error": None,
        "updated_at": now,
    }
    await db.cv_processing_queue.update_one(
        {"cv_id": cv_id},
        {"$set": doc, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    if mark_queued:
        await db.cvs.update_one({"_id": cv_id}, {"$set": {"processing_status": "queued", "updated_at": now}})


async def claim_queue_item(worker_id: int):
    now = now_utc()
    return await db.cv_processing_queue.find_one_and_update(
        {"status": "pending"},
        {"$set": {"status": "processing", "worker_id": worker_id, "started_at": now, "updated_at": now}, "$inc": {"attempts": 1}},
        sort=[("created_at", 1)],
        return_document=ReturnDocument.AFTER,
    )


async def rank_job_matches(job_id):
    rows = [row async for row in db.matching_results.find({"job_id": job_id}).sort("overall_score", -1)]
    now = now_utc()
    ops = [
        UpdateOne({"_id": row["_id"]}, {"$set": {"rank": index, "updated_at": now}})
        for index, row in enumerate(rows, 1)
    ]
    if ops:
        await db.matching_results.bulk_write(ops, ordered=False)


async def process_queue_item(item):
    cv = await db.cvs.find_one({"_id": item["cv_id"]})
    if not cv:
        raise ValueError("CV not found")
    if cv.get("processing_status") == "done" and cv.get("raw_text") and cv.get("extracted_data"):
        raw_text = cv["raw_text"]
        extracted_data = cv["extracted_data"]
    else:
        raw_text = extract_text(cv["file_path"])
        extracted_data = parse_cv_text(raw_text)
    done_at = now_utc()
    await db.cvs.update_one(
        {"_id": cv["_id"]},
        {"$set": {"raw_text": raw_text, "extracted_data": extracted_data, "processing_status": "done", "updated_at": done_at}, "$unset": {"processing_error": ""}},
    )
    if cv.get("uploaded_by_role") == "candidate":
        await db.users.update_one({"_id": cv["owner_id"]}, {"$set": {"primary_cv_id": cv["_id"], "updated_at": done_at}})
    processed_cv = {**cv, "raw_text": raw_text, "extracted_data": extracted_data, "processing_status": "done"}
    matched_jobs = 0
    try:
        async for job in db.jobs.find({"status": "open"}):
            result = compute_match(processed_cv, job)
            result.update({
                "job_id": job["_id"],
                "cv_id": cv["_id"],
                "recruiter_id": job["recruiter_id"],
                "created_at": now_utc(),
                "updated_at": now_utc(),
            })
            await db.matching_results.update_one(
                {"job_id": job["_id"], "cv_id": cv["_id"]},
                {"$set": result},
                upsert=True,
            )
            matched_jobs += 1
    except Exception as exc:
        await db.cvs.update_one({"_id": cv["_id"]}, {"$set": {"matching_error": str(exc), "updated_at": now_utc()}})
    return matched_jobs


async def cv_worker_loop(worker_id: int):
    while True:
        item = await claim_queue_item(worker_id)
        if not item:
            await asyncio.sleep(settings.cv_worker_poll_seconds)
            continue
        try:
            matched_jobs = await process_queue_item(item)
            await db.cv_processing_queue.update_one(
                {"_id": item["_id"]},
                {"$set": {"status": "done", "matched_jobs": matched_jobs, "completed_at": now_utc(), "updated_at": now_utc(), "error": None}},
            )
        except Exception as exc:
            await db.cv_processing_queue.update_one(
                {"_id": item["_id"]},
                {"$set": {"status": "failed", "error": str(exc), "completed_at": now_utc(), "updated_at": now_utc()}},
            )
            await db.cvs.update_one({"_id": item["cv_id"]}, {"$set": {"processing_status": "failed", "processing_error": str(exc), "updated_at": now_utc()}})


async def start_cv_workers():
    for worker_id in range(max(settings.cv_worker_count, 1)):
        asyncio.create_task(cv_worker_loop(worker_id + 1))
