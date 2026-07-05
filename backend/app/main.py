from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import ping_db, ensure_indexes
from app.routes import auth, users, cvs, cv_queue, jobs, matches, applications, messages, admin
from app.services.cv_worker import start_cv_workers

app = FastAPI(title="CV Match Platform API", version="1.0.0")
origins = ["http://localhost:5173", "http://localhost:3000"]
if settings.frontend_url:
    origins.extend([u.strip() for u in settings.frontend_url.split(",") if u.strip()])
app.add_middleware(CORSMiddleware, allow_origins=list(set(origins)), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    try:
        await ensure_indexes()
    except Exception as exc:
        print(f"Startup index warning: {exc}")
    await start_cv_workers()

@app.get("/health")
async def health():
    await ping_db()
    return {"status": "ok"}

for router in [auth.router, users.router, cvs.router, cv_queue.router, jobs.router, matches.router, applications.router, messages.router, admin.router]:
    app.include_router(router)
