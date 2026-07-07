import asyncio
from io import BytesIO

from bson import ObjectId
from fastapi import HTTPException, UploadFile

from app.routes import cvs


class FakeSettings:
    def __init__(self, upload_dir, max_cv_file_bytes=3):
        self.upload_dir = str(upload_dir)
        self.max_cv_file_bytes = max_cv_file_bytes


class Result:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class Collection:
    def __init__(self, rows=None):
        self.rows = rows or []

    async def insert_one(self, doc):
        row = {"_id": ObjectId(), **doc}
        self.rows.append(row)
        return Result(row["_id"])

    async def find_one(self, query):
        return next((row for row in self.rows if all(row.get(k) == v for k, v in query.items())), None)

    async def update_one(self, query, update):
        return None


def upload_file(name, data):
    return UploadFile(filename=name, file=BytesIO(data))


def test_save_cv_rejects_file_over_size_limit(monkeypatch, tmp_path):
    fake_db = type("DB", (), {"cvs": Collection([]), "users": Collection([])})()
    monkeypatch.setattr(cvs, "db", fake_db)
    monkeypatch.setattr(cvs, "settings", FakeSettings(tmp_path))

    try:
        asyncio.run(cvs.save_cv(upload_file("big.pdf", b"1234"), {"id": str(ObjectId()), "role": "recruiter"}))
    except HTTPException as exc:
        assert exc.status_code == 413
        assert exc.detail == "File exceeds 3 bytes limit"
    else:
        raise AssertionError("Expected oversized CV upload to fail")

    assert fake_db.cvs.rows == []


def test_save_cv_accepts_file_at_size_limit(monkeypatch, tmp_path):
    cv_id = ObjectId()
    fake_db = type("DB", (), {"cvs": Collection([]), "users": Collection([])})()
    queued = []
    monkeypatch.setattr(cvs, "db", fake_db)
    monkeypatch.setattr(cvs, "settings", FakeSettings(tmp_path))
    monkeypatch.setattr(cvs, "extract_text", lambda path: "Python FastAPI")
    monkeypatch.setattr(cvs, "parse_cv_text", lambda text: {"skills": ["python"]})

    async def fake_enqueue(inserted_id, owner_id, mark_queued=False):
        queued.append((inserted_id, owner_id, mark_queued))

    monkeypatch.setattr(cvs, "enqueue_cv", fake_enqueue)
    user = {"id": str(cv_id), "role": "recruiter"}

    row = asyncio.run(cvs.save_cv(upload_file("ok.pdf", b"123"), user))

    assert row["filename"] == "ok.pdf"
    assert row["queued"] is True
    assert len(fake_db.cvs.rows) == 1
    assert queued and queued[0][2] is False
