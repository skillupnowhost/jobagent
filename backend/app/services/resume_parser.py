import re
import os
import json
import io
import logging

logger = logging.getLogger(__name__)

FIELD_LABELS = {
    "name": "Name", "email": "Email", "phone": "Phone", "location": "Location",
    "linkedin_url": "LinkedIn URL", "github_url": "GitHub URL",
    "portfolio_url": "Portfolio URL", "professional_summary": "Professional Summary",
    "experience_years": "Experience (years)", "skills": "Skills",
    "experience": "Work Experience", "education": "Education",
    "certifications": "Certifications", "projects": "Projects",
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    import pdfplumber
    parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                parts.append(page_text)
    return "\n".join(parts).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()


def _extract_with_regex(text: str) -> dict:
    result = {
        "name": "", "email": "", "phone": "", "location": "",
        "linkedin_url": "", "github_url": "", "portfolio_url": "",
        "professional_summary": "", "experience_years": 0,
        "skills": [], "experience": [], "education": [],
        "certifications": [], "projects": [],
    }

    email_m = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    if email_m:
        result["email"] = email_m.group()

    phone_m = re.search(
        r'(?:\+91[\s-]?)?[6-9]\d{9}|(?:\+\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
        text,
    )
    if phone_m:
        result["phone"] = phone_m.group().strip()

    li_m = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+', text, re.IGNORECASE)
    if li_m:
        url = li_m.group()
        result["linkedin_url"] = url if url.startswith("http") else "https://" + url

    gh_m = re.search(r'(?:https?://)?(?:www\.)?github\.com/[\w-]+', text, re.IGNORECASE)
    if gh_m:
        url = gh_m.group()
        result["github_url"] = url if url.startswith("http") else "https://" + url

    from app.services.job_matcher import _extract_skills_from_text
    result["skills"] = _extract_skills_from_text(text)

    yrs_m = re.search(r'(\d+(?:\.\d+)?)\s*\+?\s*years?\s*(?:of\s+)?(?:experience|exp)', text, re.IGNORECASE)
    if yrs_m:
        result["experience_years"] = float(yrs_m.group(1))

    lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 1]
    if lines:
        result["name"] = lines[0]

    return result


def _extract_with_claude(text: str) -> dict:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""You are a resume parser. Extract structured profile information from the resume text below.

Return a JSON object with EXACTLY these keys:
- name: string (full candidate name)
- email: string
- phone: string
- location: string (city/state/country)
- linkedin_url: string (full https URL, or "")
- github_url: string (full https URL, or "")
- portfolio_url: string (full https URL, or "")
- professional_summary: string — ALWAYS write a compelling 2-4 sentence summary based on their skills, experience level, and domain even if not present in the resume
- experience_years: number (total years, calculated from date ranges)
- skills: array of strings (all technical skills, tools, languages, frameworks)
- experience: array of {{ title, company, duration, location, bullets: string[] }}
- education: array of {{ degree, institution, year, gpa }}
- certifications: array of strings
- projects: array of {{ name, description, tech_stack, link }}

Rules:
- Add "https://" to linkedin/github URLs if missing
- Use "" for missing strings, [] for missing arrays, 0 for missing numbers
- Return ONLY the raw JSON — no markdown fences, no explanation

RESUME TEXT:
{text[:8000]}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()
    response_text = re.sub(r'^```(?:json)?\s*\n?', '', response_text)
    response_text = re.sub(r'\n?```\s*$', '', response_text)

    return json.loads(response_text)


def parse_resume(file_bytes: bytes, content_type: str) -> dict:
    content_type = (content_type or "").lower()

    if "pdf" in content_type:
        text = extract_text_from_pdf(file_bytes)
    elif any(t in content_type for t in ["docx", "openxmlformats", "wordprocessingml", "msword"]):
        text = extract_text_from_docx(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="ignore")

    if not text.strip():
        raise ValueError("Could not extract text from the uploaded file")

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            data = _extract_with_claude(text)
            data["_source"] = "ai"
            return data
        except Exception as exc:
            logger.warning("Claude extraction failed, falling back to regex: %s", exc)

    data = _extract_with_regex(text)
    data["_source"] = "regex"
    return data
