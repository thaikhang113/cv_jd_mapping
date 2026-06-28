# Backend

FastAPI API for CV Match Platform.

## Local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Seed

```bash
python scripts/seed.py
```
