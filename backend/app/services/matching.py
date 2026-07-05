from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def norm_list(values):
    return {str(v).strip().lower() for v in values or [] if str(v).strip()}


def infer_cv_category(cv_data, raw_text):
    text = f"{raw_text} {' '.join(cv_data.get('skills', []))}".lower()
    if any(x in text for x in ["backend", "fastapi", "django", "flask", "api"]):
        return "backend"
    if any(x in text for x in ["frontend", "react", "vue", "angular"]):
        return "frontend"
    if any(x in text for x in ["data", "etl", "machine learning", "spark", "airflow"]):
        return "data"
    if any(x in text for x in ["devops", "kubernetes", "terraform", "ci/cd"]):
        return "devops"
    if any(x in text for x in ["qa", "tester", "selenium", "playwright"]):
        return "qa"
    return None


def infer_cv_seniority(years):
    if years >= 5:
        return "senior"
    if years <= 1:
        return "junior"
    return "mid"


def snippets(cv, job, matched):
    raw = cv.get("raw_text", "")
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    out = []
    for skill in matched[:5]:
        line = next((line for line in lines if skill.lower() in line.lower()), None)
        if line:
            out.append({"skill": skill, "source": "cv", "text": line[:180]})
    if job.get("description"):
        out.append({"source": "job", "text": job["description"][:180]})
    return out


def compute_match(cv: dict, job: dict) -> dict:
    cv_data = cv.get("extracted_data", {})
    cv_skills = norm_list(cv_data.get("skills", []))
    cv_tools = norm_list(cv_data.get("tools", []))
    job_skills = norm_list(job.get("required_skills", []))
    nice_skills = norm_list(job.get("nice_to_have_skills", []))
    matched = sorted(cv_skills & job_skills)
    missing = sorted(job_skills - cv_skills)
    nice_matches = sorted(cv_skills & nice_skills)
    matched_tools = sorted(cv_tools & (job_skills | nice_skills | cv_skills))
    skill_score = 40 if not job_skills else round((len(matched) / len(job_skills)) * 40, 2)
    cv_exp = float(cv_data.get("experience_years") or 0)
    req_exp = float(job.get("required_experience") or 0)
    experience_score = 20 if req_exp <= 0 else round(min(cv_exp / req_exp, 1) * 20, 2)
    cv_location = (cv_data.get("location") or "").lower()
    job_location = (job.get("location") or "").lower()
    location_match = bool(cv_location and (cv_location in job_location or job_location in cv_location or "remote" in job_location))
    location_score = 10 if location_match else 0
    job_text = f"{job.get('title','')} {job.get('description','')} {' '.join(job.get('required_skills', []))} {' '.join(job.get('responsibilities', []))} {' '.join(job.get('requirements', []))}"
    docs = [cv.get("raw_text", ""), job_text]
    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform(docs)
        similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        similarity = 0.0
    similarity_score = round(similarity * 30, 2)
    total = round(skill_score + experience_score + location_score + similarity_score, 2)
    cv_category = infer_cv_category(cv_data, cv.get("raw_text", ""))
    job_category = job.get("category")
    cv_seniority = infer_cv_seniority(cv_exp)
    job_seniority = job.get("seniority")
    return {
        "overall_score": min(total, 100),
        "skill_score": skill_score,
        "experience_score": experience_score,
        "location_score": location_score,
        "similarity_score": similarity_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "matched_tools": matched_tools,
        "nice_to_have_matches": nice_matches,
        "experience_match": cv_exp >= req_exp,
        "location_match": location_match,
        "relevant_experience_years": cv_exp,
        "category_match": bool(job_category and cv_category == job_category),
        "seniority_match": bool(job_seniority and cv_seniority == job_seniority),
        "evidence_snippets": snippets(cv, job, matched),
    }
