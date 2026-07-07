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


def count_in_text(text, term):
    return text.lower().count(term.lower()) if term else 0


def make_skill_items(cv_text, job_text, job_skills, nice_skills, cv_skills):
    items = []
    for skill in sorted(job_skills):
        matched = skill in cv_skills
        items.append({
            "skill": skill,
            "kind": "required",
            "required": True,
            "jd_count": max(1, count_in_text(job_text, skill)),
            "cv_count": count_in_text(cv_text, skill),
            "status": "matched" if matched else "missing",
        })
    for skill in sorted(nice_skills - job_skills):
        matched = skill in cv_skills
        items.append({
            "skill": skill,
            "kind": "nice",
            "required": False,
            "jd_count": max(1, count_in_text(job_text, skill)),
            "cv_count": count_in_text(cv_text, skill),
            "status": "matched" if matched else "missing",
        })
    return items


def section(title, description, suggestion_count, items=None, passed_text="ĐẠT"):
    return {
        "title": title,
        "description": description,
        "suggestion_count": suggestion_count,
        "status": "complete" if suggestion_count == 0 else "needs_work",
        "badge": passed_text if suggestion_count == 0 else f"{suggestion_count} đề xuất",
        "items": items or [],
    }


def build_report(cv, job, result, cv_skills, job_skills, nice_skills, cv_exp, req_exp, location_match):
    cv_data = cv.get("extracted_data", {})
    cv_text = cv.get("raw_text", "")
    job_text = f"{job.get('title','')} {job.get('description','')} {' '.join(job.get('required_skills', []))} {' '.join(job.get('nice_to_have_skills', []))}"
    skill_items = make_skill_items(cv_text, job_text, job_skills, nice_skills, cv_skills)
    missing_nice = sorted(nice_skills - cv_skills)
    skill_suggestions = len(result["missing_skills"]) + len(missing_nice)
    profile_items = []
    for key, label in [("name", "Tên"), ("email", "Email"), ("phone", "Điện thoại")]:
        if not cv_data.get(key):
            profile_items.append({"label": label, "status": "missing", "message": f"Thiếu {label.lower()} trong CV."})
    format_items = []
    if len(cv_text) > 4500:
        format_items.append({"label": "Độ dài CV", "status": "needs_work", "message": "CV hơi dài; nên rút gọn các phần ít liên quan."})
    if "\n" not in cv_text and len(cv_text) > 300:
        format_items.append({"label": "Gạch đầu dòng", "status": "needs_work", "message": "Nên tách ý thành dòng ngắn để dễ đọc hơn."})

    strengths = []
    if result["matched_skills"]:
        strengths.append(f"Kỹ năng phù hợp: {', '.join(result['matched_skills'][:4])}.")
    if cv_exp >= req_exp:
        strengths.append("Kinh nghiệm đáp ứng yêu cầu chính của JD.")
    if location_match:
        strengths.append("Địa điểm hoặc hình thức làm việc phù hợp.")
    if not strengths:
        strengths.append("CV có dữ liệu đủ để bắt đầu so khớp với JD.")

    improvements = []
    if result["missing_skills"]:
        improvements.append(f"Bổ sung hoặc làm nổi bật: {', '.join(result['missing_skills'][:5])}.")
    if cv_exp < req_exp:
        improvements.append("Làm rõ kinh nghiệm liên quan để giảm khoảng cách số năm yêu cầu.")
    if not location_match:
        improvements.append("Nêu rõ khả năng làm việc theo địa điểm hoặc remote nếu phù hợp.")
    if not improvements:
        improvements.append("Giữ CV hiện tại và tinh chỉnh từ khóa theo JD khi ứng tuyển.")

    score = round(result["overall_score"])
    if score >= 75:
        fit_summary = "CV có mức độ phù hợp tốt với JD và có khả năng vượt qua bước lọc ban đầu."
    elif score >= 55:
        fit_summary = "CV có nền tảng phù hợp nhưng cần bổ sung thêm từ khóa và bằng chứng liên quan đến JD."
    else:
        fit_summary = "CV còn thiếu nhiều tín hiệu quan trọng so với JD; nên chỉnh kỹ năng và kinh nghiệm nổi bật hơn."

    sections = {
        "content": section("Nội dung", "Kiểm tra bằng chứng, mức độ liên quan và kết quả định lượng trong CV.", 0 if result["evidence_snippets"] else 1, result["evidence_snippets"]),
        "skills": section("Kỹ năng", "So sánh kỹ năng trong JD với kỹ năng tìm thấy trong CV.", skill_suggestions, skill_items),
        "format": section("Định dạng", "Kiểm tra độ dài và cách trình bày để CV dễ đọc hơn.", len(format_items), format_items),
        "profile": section("Hồ sơ", "Kiểm tra thông tin liên hệ và dữ liệu nhận diện ứng viên.", len(profile_items), profile_items),
        "style": section("Phong cách", "Đánh giá giọng văn ở mức heuristic dựa trên dữ liệu hiện có.", 0, [{"label": "Giọng văn", "status": "complete", "message": "Không phát hiện vấn đề nổi bật."}]),
    }
    return fit_summary, strengths, improvements, sections


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
    result = {
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
    fit_summary, strengths, improvements, sections = build_report(cv, job, result, cv_skills, job_skills, nice_skills, cv_exp, req_exp, location_match)
    result.update({
        "fit_summary": fit_summary,
        "strengths": strengths,
        "improvements": improvements,
        "sections": sections,
    })
    return result
