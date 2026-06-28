import asyncio
from app.database import db
from app.dependencies import hash_password, now_utc

async def main():
    users = [
        ("Admin", "admin@example.com", "Admin123!", "admin"),
        ("Recruiter", "recruiter@example.com", "Recruiter123!", "recruiter"),
        ("Candidate", "candidate@example.com", "Candidate123!", "candidate"),
    ]
    ids = {}
    for name, email, password, role in users:
        await db.users.update_one({"email": email}, {"$set": {"name": name, "email": email, "password_hash": hash_password(password), "role": role, "is_blocked": False, "updated_at": now_utc()}, "$setOnInsert": {"created_at": now_utc()}}, upsert=True)
        ids[role] = (await db.users.find_one({"email": email}))["_id"]
    await db.jobs.delete_many({"seed": True})
    await db.jobs.insert_many([
        {"seed": True, "title": "Backend FastAPI Developer", "company_name": "DemoTech", "location": "Remote", "required_skills": ["python", "fastapi", "mongodb", "docker"], "required_experience": 2, "salary_range": "$1200-$2000", "description": "Build APIs with FastAPI MongoDB Docker.", "status": "open", "recruiter_id": ids["recruiter"], "created_at": now_utc(), "updated_at": now_utc()},
        {"seed": True, "title": "React Frontend Developer", "company_name": "DemoTech", "location": "Ho Chi Minh", "required_skills": ["react", "javascript", "css"], "required_experience": 1, "salary_range": "$900-$1500", "description": "Build dashboards with React Vite.", "status": "open", "recruiter_id": ids["recruiter"], "created_at": now_utc(), "updated_at": now_utc()},
    ])
    await db.cvs.delete_many({"seed": True})
    await db.cvs.insert_many([
        {"seed": True, "owner_id": ids["candidate"], "uploaded_by_role": "candidate", "filename": "sample-backend.txt", "file_path": "seed", "raw_text": "Candidate Email candidate@example.com Phone 0909000000 Python FastAPI MongoDB Docker 3 years Remote University", "extracted_data": {"name": "Candidate", "email": "candidate@example.com", "phone": "0909000000", "skills": ["python", "fastapi", "mongodb", "docker"], "experience_years": 3, "education": "University", "location": "Remote"}, "created_at": now_utc(), "updated_at": now_utc()},
        {"seed": True, "owner_id": ids["recruiter"], "uploaded_by_role": "recruiter", "filename": "sample-frontend.txt", "file_path": "seed", "raw_text": "Frontend React JavaScript CSS 2 years Ho Chi Minh University", "extracted_data": {"name": "Frontend Candidate", "skills": ["react", "javascript", "css"], "experience_years": 2, "education": "University", "location": "Ho Chi Minh"}, "created_at": now_utc(), "updated_at": now_utc()},
    ])
    print("Seed complete")

if __name__ == "__main__":
    asyncio.run(main())
