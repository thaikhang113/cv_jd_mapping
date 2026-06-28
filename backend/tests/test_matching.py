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
