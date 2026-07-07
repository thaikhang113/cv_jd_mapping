from bson import ObjectId
import asyncio
from app.routes import applications, matches
from app.schemas.common import ApplicationIn

class Result:
    def __init__(self, inserted_id): self.inserted_id = inserted_id

class Cursor:
    def __init__(self, rows): self.rows = list(rows)
    def sort(self, key, direction):
        self.rows.sort(key=lambda r: r.get(key, 0), reverse=direction < 0); return self
    def __aiter__(self): self.i = 0; return self
    async def __anext__(self):
        if self.i >= len(self.rows): raise StopAsyncIteration
        row = self.rows[self.i]; self.i += 1; return row

class Collection:
    def __init__(self, rows=None): self.rows = rows or []
    def _match(self, row, query):
        return all(row.get(k) == v for k, v in query.items())
    async def find_one(self, query, *args, sort=None, **kwargs):
        rows = [r for r in self.rows if self._match(r, query)]
        if sort and rows:
            key, direction = sort[0]
            rows.sort(key=lambda r: r.get(key, 0), reverse=direction < 0)
        return rows[0] if rows else None
    def find(self, query=None, *args, **kwargs):
        query = query or {}
        return Cursor([r for r in self.rows if self._match(r, query)])
    async def insert_one(self, doc):
        doc = {"_id": ObjectId(), **doc}
        self.rows.append(doc)
        return Result(doc["_id"])
    async def update_one(self, query, update, upsert=False):
        row = await self.find_one(query)
        if not row and upsert:
            row = {"_id": ObjectId(), **query}; self.rows.append(row)
        if row:
            row.update(update.get("$set", {}))
            for k, v in update.get("$inc", {}).items():
                row[k] = row.get(k, 0) + v

def test_apply_uses_primary_processed_cv(monkeypatch):
    user_id, recruiter_id, job_id, primary_cv_id = ObjectId(), ObjectId(), ObjectId(), ObjectId()
    fake_db = type("DB", (), {})()
    fake_db.jobs = Collection([{"_id": job_id, "status": "open", "recruiter_id": recruiter_id}])
    fake_db.cvs = Collection([{"_id": primary_cv_id, "owner_id": user_id, "processing_status": "done"}])
    fake_db.applications = Collection([])
    fake_db.matching_results = Collection([])
    monkeypatch.setattr(applications, "db", fake_db)

    row = asyncio.run(applications.apply(ApplicationIn(job_id=str(job_id)), {"id": str(user_id), "primary_cv_id": str(primary_cv_id)}))

    assert row["cv_id"] == str(primary_cv_id)
    assert row["status"] == "applied"

def test_recruiter_run_matches_all_processed_cvs(monkeypatch):
    recruiter_id, job_id, cv_owner = ObjectId(), ObjectId(), ObjectId()
    job = {"_id": job_id, "recruiter_id": recruiter_id, "status": "open", "title": "Backend", "description": "Python FastAPI", "required_skills": ["python"], "required_experience": 1, "location": "Remote"}
    cv = {"_id": ObjectId(), "owner_id": cv_owner, "processing_status": "done", "raw_text": "Python FastAPI 2 years Remote", "extracted_data": {"skills": ["python"], "experience_years": 2, "location": "Remote"}}
    fake_db = type("DB", (), {})()
    fake_db.jobs = Collection([job])
    fake_db.cvs = Collection([cv, {"_id": ObjectId(), "owner_id": cv_owner, "processing_status": "queued"}])
    fake_db.matching_results = Collection([])
    fake_db.match_runs = Collection([])
    monkeypatch.setattr(matches, "db", fake_db)

    run = asyncio.run(matches.run_matches({"job_id": str(job_id)}, {"id": str(recruiter_id), "role": "recruiter"}))
    asyncio.run(matches.process_match_run(ObjectId(run["run_id"])))
    status = asyncio.run(matches.match_run_status(run["run_id"], {"id": str(recruiter_id), "role": "recruiter"}))

    assert status["total"] == 1
    assert status["processed"] == 1
    assert status["results"][0]["cv_id"] == str(cv["_id"])
    assert status["results"][0]["rank"] == 1
