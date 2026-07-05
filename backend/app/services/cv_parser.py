import re
from pathlib import Path
import pdfplumber
from docx import Document

def extract_pdf_ocr(path: str) -> str:
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except Exception as exc:
        raise ValueError("PDF appears scanned; OCR dependencies unavailable") from exc
    pages = []
    with fitz.open(path) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(image, lang="vie+eng")
            if text.strip():
                pages.append(text)
    if not pages:
        raise ValueError("PDF appears scanned; OCR produced no text")
    return "\n".join(pages)

SKILLS = {
    "python","fastapi","django","flask","react","vue","angular","javascript","typescript","mongodb","postgresql","mysql","sql",
    "docker","kubernetes","azure","aws","gcp","git","github","gitlab","html","css","tailwind","node","node.js","express","java",
    "spring","c#",".net","go","rust","php","laravel","redis","rabbitmq","kafka","elasticsearch","linux","ci/cd",
    "jenkins","terraform","ansible","machine learning","deep learning","data analysis","pandas","numpy","spark","airflow",
    "power bi","tableau","excel","qa","selenium","playwright","cypress","figma","product management","scrum","agile",
    "communication","leadership","english","vietnamese"
}
TOOLS = {"docker","kubernetes","azure","aws","gcp","git","github","gitlab","jenkins","terraform","ansible","redis","rabbitmq","kafka","elasticsearch","linux","airflow","power bi","tableau","selenium","playwright","cypress","figma"}
HEADINGS = {
    "summary": {"summary", "profile", "objective", "about"},
    "experience": {"experience", "work experience", "employment", "professional experience"},
    "projects": {"projects", "project"},
    "education": {"education", "academic"},
    "certifications": {"certifications", "certification", "certificates"},
    "languages": {"languages", "language"},
    "skills": {"skills", "skill", "technical skills", "core skills", "ky nang", "cong nghe", "programming languages", "programming language", "tools", "frameworks", "technologies"},
}


def extract_text(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        with pdfplumber.open(path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text if text.strip() else extract_pdf_ocr(path)
    if suffix == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError("Unsupported file type")


def clean_lines(text: str):
    return [re.sub(r"\s+", " ", line).strip(" -\t") for line in text.splitlines() if line.strip()]


def sectionize(text: str) -> dict:
    sections = {"header": []}
    current = "header"
    for line in clean_lines(text):
        key = next((name for name, values in HEADINGS.items() if line.lower().rstrip(":") in values), None)
        if key:
            current = key
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return sections


def find_skills(text: str):
    lower = text.lower()
    return sorted(skill for skill in SKILLS if re.search(rf"(?<![a-z0-9+#.]){re.escape(skill)}(?![a-z0-9+#])", lower))


def extract_phone(text: str):
    phone_line = re.search(r"(?:phone|tel|mobile|sdt|so dien thoai)\s*[:?-]\s*([^\n]+)", text, re.I)
    candidates = []
    if phone_line:
        candidates.append(phone_line.group(1).strip())
    candidates.extend(re.findall(r"(?:\+?84|0)\s*(?:\d[\s().-]*){8,10}\d", text))
    for candidate in candidates:
        digits = re.sub(r"\D", "", candidate)
        if digits.startswith("84") and 10 <= len(digits) <= 11:
            return candidate.strip()
        if digits.startswith("0") and 10 <= len(digits) <= 11:
            return candidate.strip()
    return None

def extract_years(text: str) -> float:
    lower = text.lower()
    explicit = [float(y) for y in re.findall(r"(?<![a-z0-9])(?:experience|kinh nghiem|kinh nghiệm)?\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs|năm|nam)(?![a-z])", lower)]
    if explicit:
        return max(explicit)
    ranges = []
    for start, end in re.findall(r"\b(20\d{2}|19\d{2})\s*(?:-|to)\s*(20\d{2}|present|now|current|nay)\b", lower):
        end_year = 2026 if end in {"present", "now", "current", "nay"} else int(end)
        ranges.append(max(end_year - int(start), 0))
    return float(max(ranges, default=0))


def parse_work_experiences(lines):
    rows, current = [], None
    pattern = re.compile(r"^(?P<role>[^|:\n]+?)\s+-\s+(?P<company>[^|]+?)(?:\s*\|\s*(?P<dates>.+))?$")
    for line in lines:
        match = pattern.match(line)
        if match:
            if current:
                rows.append(current)
            current = {"role": match.group("role").strip(), "company": match.group("company").strip(), "dates": (match.group("dates") or "").strip(), "duration_years": extract_years(match.group("dates") or ""), "skills": find_skills(line), "bullets": []}
        elif current:
            current["bullets"].append(line)
            current["skills"] = sorted(set(current["skills"]) | set(find_skills(line)))
    if current:
        rows.append(current)
    return rows


def parse_projects(lines):
    projects = []
    for line in lines:
        name, _, desc = line.partition(":")
        if len(name.strip()) < 3:
            continue
        projects.append({"name": name.strip(), "description": desc.strip() or line.strip(), "tech_stack": find_skills(line)})
    return projects


def parse_education(lines):
    rows = []
    for line in lines:
        if any(w in line.lower() for w in ["university", "college", "bachelor", "master", "degree", "university"]):
            degree, _, school = line.partition(",")
            rows.append({"degree": degree.strip(), "institution": school.strip() or None})
    return rows


# ponytail: heuristic parser ceiling; upgrade path is recruiter-reviewed taxonomy plus ML/NER, not external AI API.
def parse_cv_text(text: str) -> dict:
    sections = sectionize(text)
    lines = clean_lines(text)
    lower = text.lower()
    email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone = extract_phone(text)
    skills = find_skills(text)
    work = parse_work_experiences(sections.get("experience", []))
    projects = parse_projects(sections.get("projects", []))
    education = parse_education(sections.get("education", []))
    certifications = [line for line in sections.get("certifications", []) if len(line) > 2]
    languages = re.split(r",|/|;", " ".join(sections.get("languages", []))) if sections.get("languages") else []
    location = next((line for line in lines if any(w in line.lower() for w in ["hanoi", "ha noi", "ho chi minh", "danang", "da nang", "remote", "hybrid"])), None)
    return {
        "name": lines[0][:80] if lines else None,
        "email": email.group(0) if email else None,
        "phone": phone,
        "summary": " ".join(sections.get("summary", [])[:3]) or None,
        "skills": skills,
        "tools": sorted(set(skills) & TOOLS),
        "languages": [x.strip() for x in languages if x.strip()],
        "experience_years": max([extract_years(text)] + [w.get("duration_years", 0) for w in work], default=0),
        "work_experiences": work,
        "projects": projects,
        "education": education,
        "certifications": certifications,
        "location": location,
        "raw_sections": sections,
        "education_summary": "detected" if education or any(w in lower for w in ["university", "college", "bachelor", "master", "university"]) else None,
    }
