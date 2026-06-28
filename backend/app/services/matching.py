from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def norm_list(values):
    return {str(v).strip().lower() for v in values or [] if str(v).strip()}

def compute_match(cv: dict, job: dict) -> dict:
    cv_data = cv.get("extracted_data", {})
    cv_skills = norm_list(cv_data.get("skills", []))
    job_skills = norm_list(job.get("required_skills", []))
    matched = sorted(cv_skills & job_skills)
    missing = sorted(job_skills - cv_skills)
    skill_score = 40 if not job_skills else round((len(matched) / len(job_skills)) * 40, 2)
    cv_exp = float(cv_data.get("experience_years") or 0)
    req_exp = float(job.get("required_experience") or 0)
    experience_score = 20 if req_exp <= 0 else round(min(cv_exp / req_exp, 1) * 20, 2)
    cv_location = (cv_data.get("location") or "").lower()
    job_location = (job.get("location") or "").lower()
    location_match = bool(cv_location and (cv_location in job_location or job_location in cv_location or "remote" in job_location))
    location_score = 10 if location_match else 0
    docs = [cv.get("raw_text", ""), f"{job.get('title','')} {job.get('description','')} {' '.join(job.get('required_skills', []))}"]
    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform(docs)
        similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    except ValueError:
        similarity = 0.0
    similarity_score = round(similarity * 30, 2)
    total = round(skill_score + experience_score + location_score + similarity_score, 2)
    return {
        "overall_score": min(total, 100),
        "skill_score": skill_score,
        "experience_score": experience_score,
        "location_score": location_score,
        "similarity_score": similarity_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "experience_match": cv_exp >= req_exp,
        "location_match": location_match,
    }
