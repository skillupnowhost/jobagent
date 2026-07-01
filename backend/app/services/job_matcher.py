import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SKILL_SYNONYMS = {
    "selenium": ["selenium webdriver", "selenium ide", "selenium grid"],
    "python": ["python3", "python 3"],
    "javascript": ["js", "ecmascript"],
    "typescript": ["ts"],
    "react": ["reactjs", "react.js"],
    "cypress": ["cypress.io"],
    "api testing": ["rest api testing", "api automation"],
    "postman": ["postman api"],
    "jira": ["atlassian jira"],
    "git": ["github", "gitlab", "bitbucket"],
    "ci/cd": ["continuous integration", "continuous deployment", "jenkins", "github actions"],
    "agile": ["scrum", "kanban", "sprint"],
    "sql": ["mysql", "postgresql", "sql server"],
    "manual testing": ["functional testing", "regression testing"],
    "automation testing": ["test automation", "automated testing"],
    "java": ["core java"],
    "testng": ["test ng"],
    "cucumber": ["bdd", "gherkin"],
    "appium": ["mobile testing", "mobile automation"],
    "rest assured": ["restassured"],
    "performance testing": ["load testing", "jmeter", "gatling"],
}

MNC_COMPANIES = {
    "google", "microsoft", "amazon", "apple", "meta", "facebook", "netflix",
    "adobe", "salesforce", "oracle", "ibm", "sap", "cisco", "intel",
    "qualcomm", "samsung", "sony", "tcs", "infosys", "wipro", "hcl",
    "cognizant", "tech mahindra", "capgemini", "accenture", "deloitte",
    "ey", "pwc", "kpmg", "mckinsey", "bain", "bcg", "goldman sachs",
    "jpmorgan", "morgan stanley", "barclays", "hsbc", "uber", "airbnb",
    "spotify", "twitter", "linkedin", "paypal", "visa", "mastercard",
    "nvidia", "amd", "vmware", "dell", "hp", "lenovo", "philips",
    "siemens", "bosch", "honeywell", "ge", "3m", "johnson & johnson",
    "pfizer", "novartis", "roche", "unilever", "procter & gamble",
    "nestle", "coca-cola", "pepsico", "walmart", "target", "costco",
    "flipkart", "swiggy", "zomato", "paytm", "razorpay", "cred",
    "byju's", "ola", "meesho", "phonepe", "groww", "zerodha",
    "freshworks", "zoho", "mindtree", "mphasis", "ltimindtree",
    "thoughtworks", "epam", "globallogic", "nagarro", "publicis sapient",
}


def _expand_skills(skills: list[str]) -> set[str]:
    expanded = set()
    for skill in skills:
        expanded.add(skill.lower().strip())
        for canonical, synonyms in SKILL_SYNONYMS.items():
            if skill.lower().strip() in [canonical] + [s.lower() for s in synonyms]:
                expanded.add(canonical)
                expanded.update(s.lower() for s in synonyms)
    return expanded


def _extract_skills_from_text(text: str) -> list[str]:
    all_known = set()
    for canonical, syns in SKILL_SYNONYMS.items():
        all_known.add(canonical.lower())
        all_known.update(s.lower() for s in syns)

    found = []
    text_lower = text.lower()
    for skill in sorted(all_known, key=len, reverse=True):
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def _extract_experience_requirement(text: str) -> tuple[float | None, float | None]:
    patterns = [
        r'(\d+\.?\d*)\s*[-–to]+\s*(\d+\.?\d*)\s*(?:years?|yrs?)',
        r'(\d+\.?\d*)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)',
        r'minimum\s*(?:of)?\s*(\d+\.?\d*)\s*(?:years?|yrs?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return float(groups[0]), float(groups[1])
            return float(groups[0]), None
    return None, None


def calculate_match_score(user_profile: dict, job: dict) -> dict:
    user_skills_raw = user_profile.get("skills", [])
    if user_skills_raw and isinstance(user_skills_raw[0], dict):
        user_skills_flat = []
        for cat in user_skills_raw:
            user_skills_flat.extend(cat.get("items", []))
        user_skills_raw = user_skills_flat

    user_skills = _expand_skills(user_skills_raw)

    job_desc = f"{job.get('description', '')} {job.get('requirements', '')}"
    job_skills_from_desc = _extract_skills_from_text(job_desc)
    job_required = job.get("required_skills", [])
    all_job_skills = list(set([s.lower() for s in job_required] + job_skills_from_desc))

    if not all_job_skills:
        all_job_skills = job_skills_from_desc

    # --- Skill match score (40%) ---
    if all_job_skills:
        matched = [s for s in all_job_skills if s in user_skills]
        skill_score = len(matched) / len(all_job_skills) * 100
    else:
        skill_score = 50
        matched = []

    # --- Experience match score (20%) ---
    user_exp = user_profile.get("experience_years", 2.6)
    exp_min, exp_max = _extract_experience_requirement(job_desc)
    if exp_min is not None:
        if exp_max and user_exp >= exp_min and user_exp <= exp_max:
            exp_score = 100
        elif user_exp >= (exp_min if exp_min else 0):
            exp_score = 100
        elif user_exp >= (exp_min - 1):
            exp_score = 70
        else:
            exp_score = max(0, 100 - (exp_min - user_exp) * 20)
    else:
        exp_score = 75

    # --- Title relevance (20%) ---
    title = job.get("title", "").lower()
    relevant_titles = [
        "qa", "test", "quality", "sdet", "automation", "testing",
        "quality assurance", "software test", "ui test", "manual test",
    ]
    title_score = 100 if any(t in title for t in relevant_titles) else 40

    # --- NLP text similarity (20%) ---
    user_text = " ".join(user_skills_raw) + " " + user_profile.get("professional_summary", "")
    if job_desc.strip():
        try:
            vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
            tfidf = vectorizer.fit_transform([user_text, job_desc])
            nlp_score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0] * 100
        except Exception:
            nlp_score = 50
    else:
        nlp_score = 50

    total = (skill_score * 0.4) + (exp_score * 0.2) + (title_score * 0.2) + (nlp_score * 0.2)

    # --- Company bonus ---
    company = job.get("company", "").lower()
    is_mnc = any(mnc in company for mnc in MNC_COMPANIES)
    if is_mnc:
        total = min(100, total + 5)

    missing_skills = [s for s in all_job_skills if s not in user_skills]

    return {
        "total_score": round(total, 2),
        "skill_score": round(skill_score, 2),
        "experience_score": round(exp_score, 2),
        "title_score": round(title_score, 2),
        "nlp_score": round(nlp_score, 2),
        "matched_skills": list(set(matched)),
        "missing_skills": list(set(missing_skills)),
        "is_mnc": is_mnc,
        "experience_requirement": {"min": exp_min, "max": exp_max},
        "recommendation": _get_recommendation(total),
    }


def _get_recommendation(score: float) -> str:
    if score >= 80:
        return "Excellent match — apply immediately"
    elif score >= 60:
        return "Good match — strongly recommended"
    elif score >= 40:
        return "Moderate match — worth applying"
    elif score >= 25:
        return "Partial match — apply if interested in the company"
    else:
        return "Low match — consider skipping"


def should_apply(match_result: dict, min_score: float = 25.0) -> bool:
    if match_result["is_mnc"] and match_result["total_score"] >= 20:
        return True
    return match_result["total_score"] >= min_score
