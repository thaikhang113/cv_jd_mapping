import re
from pathlib import Path
import pdfplumber
from docx import Document

SKILLS = {"python","fastapi","react","javascript","typescript","mongodb","sql","docker","azure","aws","git","html","css","node","java","c#","excel","communication","leadership","machine learning","data analysis"}

def extract_text(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    if suffix == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError("Unsupported file type")

def parse_cv_text(text: str) -> dict:
    lower = text.lower()
    email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone = re.search(r"(\+?\d[\d\s().-]{7,}\d)", text)
    years = re.findall(r"(\d+(?:\.\d+)?)\+?\s*(?:years|year|yrs|năm)", lower)
    found_skills = sorted(skill for skill in SKILLS if skill in lower)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return {
        "name": lines[0][:80] if lines else None,
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
        "skills": found_skills,
        "experience_years": max([float(y) for y in years], default=0),
        "education": "detected" if any(w in lower for w in ["university", "college", "bachelor", "master", "đại học"]) else None,
        "location": next((line for line in lines if any(w in line.lower() for w in ["hanoi", "ha noi", "ho chi minh", "danang", "remote"])), None),
    }
