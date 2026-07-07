from app.services.matching import compute_match

def test_compute_match_scores_skill_experience_location_similarity():
    cv = {"raw_text": "Python FastAPI MongoDB Docker backend", "extracted_data": {"skills": ["python", "fastapi", "mongodb"], "experience_years": 3, "location": "Remote"}}
    job = {"title": "Backend", "description": "Python FastAPI Docker", "required_skills": ["python", "fastapi", "docker"], "required_experience": 2, "location": "Remote"}
    result = compute_match(cv, job)
    assert result["skill_score"] == 26.67
    assert result["experience_score"] == 20
    assert result["location_score"] == 10
    assert result["overall_score"] > 56
    assert result["matched_skills"] == ["fastapi", "python"]
    assert result["missing_skills"] == ["docker"]


def test_compute_match_returns_cake_style_report_sections():
    cv = {"raw_text": "Python FastAPI API Remote", "extracted_data": {"skills": ["python", "fastapi"], "experience_years": 1, "location": "Remote", "email": "a@b.com"}}
    job = {"title": "Backend", "company_name": "Acme", "description": "Python FastAPI Docker", "required_skills": ["python", "fastapi", "docker"], "nice_to_have_skills": ["mongodb"], "required_experience": 2, "location": "Remote"}

    result = compute_match(cv, job)

    assert result["fit_summary"]
    assert result["strengths"]
    assert result["improvements"]
    assert set(result["sections"]) == {"content", "skills", "format", "profile", "style"}
    assert result["sections"]["skills"]["suggestion_count"] == 2
    docker = next(item for item in result["sections"]["skills"]["items"] if item["skill"] == "docker")
    assert docker["jd_count"] >= 1
    assert docker["cv_count"] == 0
    assert docker["status"] == "missing"


def test_compute_match_marks_skills_section_complete_when_no_missing_skills():
    cv = {"raw_text": "Python FastAPI Docker", "extracted_data": {"skills": ["python", "fastapi", "docker"], "experience_years": 3, "location": "Remote", "phone": "123"}}
    job = {"title": "Backend", "description": "Python FastAPI Docker", "required_skills": ["python", "fastapi", "docker"], "required_experience": 2, "location": "Remote"}

    result = compute_match(cv, job)

    assert result["missing_skills"] == []
    assert result["sections"]["skills"]["status"] == "complete"
    assert result["sections"]["skills"]["suggestion_count"] == 0
