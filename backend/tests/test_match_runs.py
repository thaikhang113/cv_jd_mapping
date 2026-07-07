import asyncio
from bson import ObjectId
from app.routes import matches


class Result:
    def __init__(self, inserted_id): self.inserted_id = inserted_id


class Cursor:
    def __init__(self, rows): self.rows = list(rows)
    def sort(self, key, direction): self.rows.sort(key=lambda r: r.get(key, 0), reverse=direction < 0); return self
    def skip(self, count): self.rows = self.rows[count:]; return self
    def limit(self, count): self.rows = self.rows[:count]; return self
    def __aiter__(self): self.i = 0; return self
    async def __anext__(self):
        if self.i >= len(self.rows): raise StopAsyncIteration
        row = self.rows[self.i]; self.i += 1; return row


class Collection:
    def __init__(self, rows=None): self.rows = rows or []
    def _match(self, row, query):
        for key, value in (query or {}).items():
            if isinstance(value, dict) and "$in" in value:
                if row.get(key) not in value["$in"]: return False
            elif row.get(key) != value:
                return False
        return True
    async def count_documents(self, query):
        return len([r for r in self.rows if self._match(r, query)])
    async def find_one(self, query, *args, sort=None, **kwargs):
        rows = [r for r in self.rows if self._match(r, query)]
        if sort and rows:
            key, direction = sort[0]; rows.sort(key=lambda r: r.get(key, 0), reverse=direction < 0)
        return rows[0] if rows else None
    def find(self, query=None, *args, **kwargs):
        return Cursor([r for r in self.rows if self._match(r, query or {})])
    async def insert_one(self, doc):
        row = {"_id": ObjectId(), **doc}
        self.rows.append(row)
        return Result(row["_id"])
    async def update_one(self, query, update, upsert=False):
        row = await self.find_one(query)
        if not row and upsert:
            row = {"_id": ObjectId(), **query}; self.rows.append(row)
        if row:
            row.update(update.get("$set", {}))
            for key, value in update.get("$inc", {}).items():
                row[key] = row.get(key, 0) + value


def make_db(job, cvs):
    fake_db = type("DB", (), {})()
    fake_db.jobs = Collection([job])
    fake_db.cvs = Collection(cvs)
    fake_db.matching_results = Collection([])
    fake_db.match_runs = Collection([])
    return fake_db


def test_run_matches_returns_progress_job_without_waiting(monkeypatch):
    recruiter_id, job_id = ObjectId(), ObjectId()
    job = {"_id": job_id, "recruiter_id": recruiter_id, "title": "Backend", "description": "Python", "required_skills": ["python"]}
    cvs = [
        {"_id": ObjectId(), "processing_status": "done"},
        {"_id": ObjectId(), "processing_status": "queued"},
    ]
    fake_db = make_db(job, cvs)
    monkeypatch.setattr(matches, "db", fake_db)

    row = asyncio.run(matches.run_matches({"job_id": str(job_id)}, {"id": str(recruiter_id), "role": "recruiter"}, None))

    assert row["run_id"]
    assert row["total"] == 1
    assert row["processed"] == 0
    assert row["status"] == "queued"
    assert fake_db.match_runs.rows[0]["job_id"] == job_id


def test_process_match_run_updates_progress_and_returns_report(monkeypatch):
    recruiter_id, job_id = ObjectId(), ObjectId()
    cv1, cv2 = ObjectId(), ObjectId()
    job = {"_id": job_id, "recruiter_id": recruiter_id, "title": "Backend", "description": "Python FastAPI", "required_skills": ["python"], "required_experience": 1, "location": "Remote"}
    cvs = [
        {"_id": cv1, "processing_status": "done", "raw_text": "Python FastAPI 3 years Remote", "extracted_data": {"name": "Good", "skills": ["python"], "experience_years": 3, "location": "Remote"}},
        {"_id": cv2, "processing_status": "done", "raw_text": "Excel", "extracted_data": {"name": "Weak", "skills": ["excel"], "experience_years": 0}},
    ]
    fake_db = make_db(job, cvs)
    monkeypatch.setattr(matches, "db", fake_db)
    created = asyncio.run(matches.run_matches({"job_id": str(job_id)}, {"id": str(recruiter_id), "role": "recruiter"}, None))

    asyncio.run(matches.process_match_run(ObjectId(created["run_id"])))
    status = asyncio.run(matches.match_run_status(created["run_id"], {"id": str(recruiter_id), "role": "recruiter"}))

    assert status["status"] == "done"
    assert status["processed"] == 2
    assert status["succeeded"] == 2
    assert status["percent"] == 100
    assert len(status["results"]) == 2
    assert status["results"][0]["rank"] == 1
    assert "fit_summary" in status["results"][0]
    assert "sections" in status["results"][0]
