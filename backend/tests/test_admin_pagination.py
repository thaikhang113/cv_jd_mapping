import asyncio
from bson import ObjectId
from app.routes import admin


class Cursor:
    def __init__(self, rows): self.rows = list(rows)
    def skip(self, count): self.rows = self.rows[count:]; return self
    def limit(self, count): self.rows = self.rows[:count]; return self
    def __aiter__(self): self.i = 0; return self
    async def __anext__(self):
        if self.i >= len(self.rows): raise StopAsyncIteration
        row = self.rows[self.i]; self.i += 1; return row


class Collection:
    def __init__(self, rows): self.rows = rows
    def find(self, query=None): return Cursor(self.rows)


def test_admin_matches_caps_default_page(monkeypatch):
    fake_db = type("DB", (), {})()
    fake_db.matching_results = Collection([{"_id": ObjectId(), "rank": i} for i in range(150)])
    monkeypatch.setattr(admin, "db", fake_db)

    rows = asyncio.run(admin.matches())

    assert len(rows) == 100
