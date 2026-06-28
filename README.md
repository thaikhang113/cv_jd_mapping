# CV Match Platform

Mini recruitment platform for candidates, recruiters, and admins. FARM stack: FastAPI, React/Vite, MongoDB.

## Tech Stack

- Backend: FastAPI, Motor async MongoDB, JWT, passlib/bcrypt
- Frontend: React, Vite, Axios, React Router, Context API
- Matching: TF-IDF + cosine similarity via scikit-learn, plus skill/experience/location scoring
- Files: PDF via pdfplumber, DOCX via python-docx
- Deployment target: MongoDB Atlas, Azure App Service, Vercel

## Structure

```text
backend/app/routes      REST APIs
backend/app/services    CV parsing and matching
backend/scripts/seed.py demo data
frontend/src/pages      role pages
frontend/src/context    auth state
docker-compose.yml      local mongo/backend/frontend
```

## Local Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- MongoDB: mongodb://localhost:27017

## Local Without Docker

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

## Seed Accounts

- admin@example.com / Admin123!
- recruiter@example.com / Recruiter123!
- candidate@example.com / Candidate123!

Run:

```bash
cd backend
python scripts/seed.py
```

## Main APIs

- Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`
- CVs: `/api/cvs/upload`, `/api/cvs/upload-multiple`, `/api/cvs/my`
- Jobs: `/api/jobs`, `/api/jobs/my`, `/api/jobs/{job_id}`
- Matching: `/api/matches/run`, `/api/matches/job/{job_id}`, `/api/matches/my`
- Applications: `/api/applications`, `/api/applications/my`
- Messages: `/api/conversations`, `/api/messages`
- Admin: `/api/admin/stats`, `/api/admin/users`, `/api/admin/cvs`, `/api/admin/jobs`, `/api/admin/matches`, `/api/admin/applications`

## Environment Variables

Backend: `MONGO_URI`, `DATABASE_NAME`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `FRONTEND_URL`, `UPLOAD_DIR`.

Frontend: `VITE_API_BASE_URL`.

## Submission Links

- GitHub repository: pending push
- Frontend Vercel: pending deploy
- Backend Swagger: pending deploy
- MongoDB Atlas: configured by env only; do not commit URI
