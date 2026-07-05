from app.services.cv_parser import parse_cv_text
from app.services.jd_parser import parse_jd_text
from app.services.matching import compute_match


def test_parse_cv_text_extracts_itemized_profile():
    text = """
    Cao Thai Khang
    Email: khang@example.com | Phone: +84 901 234 567 | Ho Chi Minh City
    Summary
    Data Engineer with 4 years building Python, FastAPI, MongoDB and Docker systems.
    Experience
    Data Engineer - ABC Tech | 2021 - 2024
    - Built ETL pipelines with Python, SQL, Azure, Docker.
    Backend Intern - Demo Lab | 2020 - 2021
    - Developed FastAPI services and MongoDB reports.
    Projects
    CV Match Platform: FastAPI, React, MongoDB, Docker matching system.
    Education
    Bachelor of Computer Science, Demo University
    Certifications
    Azure Fundamentals
    Languages
    English, Vietnamese
    """

    data = parse_cv_text(text)

    assert data["name"] == "Cao Thai Khang"
    assert data["experience_years"] >= 4
    assert {"python", "fastapi", "mongodb", "docker", "azure", "sql"}.issubset(set(data["skills"]))
    assert data["work_experiences"][0]["role"] == "Data Engineer"
    assert data["work_experiences"][0]["company"] == "ABC Tech"
    assert "CV Match Platform" in data["projects"][0]["name"]
    assert data["education"][0]["degree"] == "Bachelor of Computer Science"
    assert "Azure Fundamentals" in data["certifications"]
    assert "English" in data["languages"]


def test_parse_jd_text_extracts_job_draft():
    text = """
    Senior Backend Engineer
    Company: MatchPoint SaaS
    Location: Ho Chi Minh City / Hybrid
    Salary: 1500-2500 USD
    Job Type: Full-time
    Responsibilities
    - Build recruitment APIs with Python and FastAPI.
    - Own MongoDB data models and Docker deployments on Azure.
    Requirements
    - 5+ years backend experience.
    - Strong Python, FastAPI, MongoDB, Docker, Azure.
    Nice to have
    - React and data analysis.
    Benefits
    - 13th month salary and flexible work.
    """

    data = parse_jd_text(text)

    assert data["title"] == "Senior Backend Engineer"
    assert data["company_name"] == "MatchPoint SaaS"
    assert data["seniority"] == "senior"
    assert data["category"] == "backend"
    assert data["work_mode"] == "hybrid"
    assert data["required_experience"] == 5
    assert {"python", "fastapi", "mongodb", "docker", "azure"}.issubset(set(data["required_skills"]))
    assert "react" in data["nice_to_have_skills"]
    assert data["responsibilities"]
    assert data["requirements"]
    assert data["benefits"]
    assert data["parse_confidence"] >= 70


def test_compute_match_uses_deep_fields_and_evidence():
    cv = {
        "raw_text": "Python FastAPI MongoDB Docker Azure backend systems",
        "extracted_data": {
            "skills": ["python", "fastapi", "mongodb", "docker", "azure"],
            "tools": ["docker", "azure"],
            "experience_years": 5,
            "location": "Ho Chi Minh City",
            "work_experiences": [{"role": "Backend Engineer", "bullets": ["Built FastAPI APIs"]}],
        },
    }
    job = {
        "title": "Senior Backend Engineer",
        "description": "Build FastAPI APIs on Azure",
        "required_skills": ["python", "fastapi", "mongodb", "docker"],
        "nice_to_have_skills": ["azure", "react"],
        "required_experience": 4,
        "location": "Ho Chi Minh City",
        "category": "backend",
        "seniority": "senior",
    }

    result = compute_match(cv, job)

    assert result["matched_tools"] == ["azure", "docker"]
    assert result["nice_to_have_matches"] == ["azure"]
    assert result["category_match"] is True
    assert result["seniority_match"] is True
    assert result["relevant_experience_years"] == 5
    assert result["evidence_snippets"]
