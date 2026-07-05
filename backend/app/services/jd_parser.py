import re
from app.services.cv_parser import clean_lines, sectionize, find_skills, extract_text

JOB_HEADINGS = {
    "responsibilities": {"responsibilities", "what you will do", "duties"},
    "requirements": {"requirements", "qualifications", "must have", "required"},
    "nice_to_have": {"nice to have", "preferred", "bonus"},
    "benefits": {"benefits", "perks", "why join us"},
}
CATEGORIES = {
    "backend": {"backend", "fastapi", "django", "flask", "node", "spring", "api"},
    "frontend": {"frontend", "react", "vue", "angular", "html", "css"},
    "data": {"data", "etl", "machine learning", "pandas", "spark", "airflow"},
    "devops": {"devops", "docker", "kubernetes", "terraform", "azure", "aws", "ci/cd"},
    "qa": {"qa", "tester", "selenium", "playwright", "cypress"},
    "product": {"product", "scrum", "agile", "figma"},
}


def jd_sections(text: str):
    sections = {"header": []}
    current = "header"
    for line in clean_lines(text):
        key = next((name for name, values in JOB_HEADINGS.items() if line.lower().rstrip(":") in values), None)
        if key:
            current = key
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return sections


def field_value(lines, name):
    pattern = re.compile(rf"^{name}\s*:\s*(.+)$", re.I)
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return None


def infer_seniority(text):
    lower = text.lower()
    if "senior" in lower or "lead" in lower or "principal" in lower:
        return "senior"
    if "junior" in lower or "intern" in lower or "fresher" in lower:
        return "junior"
    if "middle" in lower or "mid" in lower:
        return "mid"
    return "mid"


def infer_category(text, skills):
    lower = text.lower()
    scores = {name: sum(1 for key in keys if key in lower or key in skills) for name, keys in CATEGORIES.items()}
    return max(scores, key=scores.get) if max(scores.values(), default=0) else "other"


def infer_work_mode(text):
    lower = text.lower()
    if "hybrid" in lower:
        return "hybrid"
    if "remote" in lower:
        return "remote"
    return "onsite"


def bullets(lines):
    return [line for line in lines if len(line) > 2 and not re.match(r"^(company|location|salary|job type)\s*:", line, re.I)]


def parse_jd_text(text: str) -> dict:
    lines = clean_lines(text)
    sections = jd_sections(text)
    header = sections.get("header", [])
    title = next((line for line in header if not re.match(r"^(company|location|salary|job type)\s*:", line, re.I)), lines[0] if lines else "Untitled Job")
    company = field_value(header, "company") or "Unknown Company"
    location = field_value(header, "location") or next((line for line in lines if any(x in line.lower() for x in ["ho chi minh", "hanoi", "remote", "hybrid"])), "")
    salary = field_value(header, "salary")
    job_type = field_value(header, "job type") or "Full-time"
    req_text = "\n".join(sections.get("requirements", []))
    nice_text = "\n".join(sections.get("nice_to_have", []))
    required_skills = find_skills(req_text or text)
    nice = [s for s in find_skills(nice_text) if s not in required_skills]
    years = re.findall(r"(\d+(?:\.\d+)?)\+?\s*(?:years|year|yrs|nam)", text.lower())
    responsibilities = bullets(sections.get("responsibilities", []))
    requirements = bullets(sections.get("requirements", []))
    benefits = bullets(sections.get("benefits", []))
    filled = sum(bool(x) for x in [title, company != "Unknown Company", location, required_skills, years, responsibilities, requirements])
    confidence = min(100, 30 + filled * 10)
    description = "\n".join(responsibilities + requirements + sections.get("nice_to_have", []) + benefits) or text.strip()
    skills_set = set(required_skills + nice)
    return {
        "title": title,
        "company_name": company,
        "location": location,
        "required_skills": required_skills,
        "nice_to_have_skills": nice,
        "required_experience": max([float(y) for y in years], default=0),
        "salary_range": salary,
        "description": description,
        "status": "open",
        "category": infer_category(text, skills_set),
        "seniority": infer_seniority(title + "\n" + text),
        "job_type": job_type,
        "work_mode": infer_work_mode(text),
        "responsibilities": responsibilities,
        "requirements": requirements,
        "benefits": benefits,
        "education_requirements": [line for line in requirements if any(w in line.lower() for w in ["bachelor", "degree", "university", "college"])],
        "raw_text": text,
        "parsed_sections": sections,
        "parse_confidence": confidence,
    }
