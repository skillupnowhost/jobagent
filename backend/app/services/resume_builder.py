import os
import re
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


RESUMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resumes")
os.makedirs(RESUMES_DIR, exist_ok=True)


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="Name",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=2,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="ContactInfo",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor("#444444"),
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        fontSize=11,
        leading=14,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold",
        borderWidth=0,
    ))
    styles.add(ParagraphStyle(
        name="JobTitle",
        fontSize=10,
        leading=13,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#2d2d2d"),
        spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name="CompanyLine",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#555555"),
        fontName="Helvetica-Oblique",
        spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="BulletPoint",
        fontSize=9,
        leading=12,
        leftIndent=15,
        bulletIndent=5,
        spaceAfter=2,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor("#333333"),
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        fontSize=9,
        leading=12,
        alignment=TA_JUSTIFY,
        spaceAfter=4,
        textColor=colors.HexColor("#333333"),
    ))
    styles.add(ParagraphStyle(
        name="SkillCategory",
        fontSize=9,
        leading=12,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#2d2d2d"),
    ))
    styles.add(ParagraphStyle(
        name="SkillList",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#444444"),
    ))
    return styles


def _section_divider():
    return HRFlowable(
        width="100%", thickness=0.5, lineCap="round",
        color=colors.HexColor("#1a1a2e"), spaceAfter=4, spaceBefore=2,
    )


def _spell_check_text(text: str) -> list[str]:
    errors = []
    common_misspellings = {
        "teh": "the", "recieve": "receive", "occured": "occurred",
        "seperate": "separate", "definately": "definitely",
        "accomodate": "accommodate", "occurence": "occurrence",
        "managment": "management", "developement": "development",
        "enviroment": "environment", "responsiblity": "responsibility",
        "acheive": "achieve", "bussiness": "business",
        "calender": "calendar", "colum": "column",
    }
    words = re.findall(r"[a-zA-Z]+", text.lower())
    for word in words:
        if word in common_misspellings:
            errors.append(f"Possible misspelling: '{word}' → '{common_misspellings[word]}'")
    return errors


def _tailor_summary(profile: dict, job: dict | None) -> str:
    base = profile.get("professional_summary", "")
    if not job:
        return base

    job_title = job.get("title", "")
    company = job.get("company", "")
    required_skills = job.get("required_skills", [])

    user_skills = [s.lower() for s in profile.get("skills", [])]
    matched = [s for s in required_skills if s.lower() in user_skills]

    if matched:
        skills_str = ", ".join(matched[:5])
        return (
            f"Results-driven QA professional with {profile.get('experience_years', 2.6)}+ years of experience "
            f"in software testing and quality assurance. Proficient in {skills_str}, with a proven track record "
            f"of delivering high-quality software solutions. Seeking to leverage expertise in "
            f"{'the ' + job_title + ' role' if job_title else 'a challenging QA role'}"
            f"{' at ' + company if company else ''} to drive quality and efficiency."
        )
    return base


def _tailor_experience_bullets(experience: list[dict], job: dict | None) -> list[dict]:
    if not job:
        return experience

    required_skills = [s.lower() for s in job.get("required_skills", [])]
    tailored = []

    for exp in experience:
        new_exp = exp.copy()
        bullets = exp.get("bullets", [])
        scored = []
        for bullet in bullets:
            relevance = sum(1 for skill in required_skills if skill in bullet.lower())
            scored.append((relevance, bullet))
        scored.sort(key=lambda x: x[0], reverse=True)
        new_exp["bullets"] = [b for _, b in scored]
        tailored.append(new_exp)

    return tailored


def generate_resume_pdf(profile: dict, job: dict | None = None, filename: str | None = None) -> dict:
    styles = _build_styles()
    all_text_errors = []

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company = (job.get("company", "general") if job else "general").replace(" ", "_")
        filename = f"resume_{company}_{timestamp}.pdf"

    filepath = os.path.join(RESUMES_DIR, filename)
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    elements = []

    # --- Header ---
    elements.append(Paragraph(profile.get("name", "Your Name"), styles["Name"]))

    contact_parts = []
    if profile.get("email"):
        contact_parts.append(profile["email"])
    if profile.get("phone"):
        contact_parts.append(profile["phone"])
    if profile.get("location"):
        contact_parts.append(profile["location"])
    elements.append(Paragraph(" | ".join(contact_parts), styles["ContactInfo"]))

    link_parts = []
    if profile.get("linkedin_url"):
        link_parts.append(f'<a href="{profile["linkedin_url"]}" color="#0077b5">LinkedIn</a>')
    if profile.get("github_url"):
        link_parts.append(f'<a href="{profile["github_url"]}" color="#333">GitHub</a>')
    if profile.get("portfolio_url"):
        link_parts.append(f'<a href="{profile["portfolio_url"]}" color="#333">Portfolio</a>')
    if link_parts:
        elements.append(Paragraph(" | ".join(link_parts), styles["ContactInfo"]))

    elements.append(_section_divider())

    # --- Professional Summary ---
    summary = _tailor_summary(profile, job)
    if summary:
        elements.append(Paragraph("PROFESSIONAL SUMMARY", styles["SectionHeading"]))
        elements.append(_section_divider())
        all_text_errors.extend(_spell_check_text(summary))
        elements.append(Paragraph(summary, styles["BodyText2"]))

    # --- Skills ---
    skills = profile.get("skills", [])
    if skills:
        elements.append(Paragraph("TECHNICAL SKILLS", styles["SectionHeading"]))
        elements.append(_section_divider())

        if isinstance(skills[0], dict):
            for cat in skills:
                cat_name = cat.get("category", "")
                cat_skills = ", ".join(cat.get("items", []))
                row = [[
                    Paragraph(f"<b>{cat_name}:</b>", styles["SkillCategory"]),
                    Paragraph(cat_skills, styles["SkillList"]),
                ]]
                t = Table(row, colWidths=[1.6 * inch, 5.0 * inch])
                t.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]))
                elements.append(t)
        else:
            if job and job.get("required_skills"):
                required = {s.lower() for s in job["required_skills"]}
                highlighted = []
                for s in skills:
                    if s.lower() in required:
                        highlighted.append(f"<b>{s}</b>")
                    else:
                        highlighted.append(s)
                skills_text = " • ".join(highlighted)
            else:
                skills_text = " • ".join(skills)
            elements.append(Paragraph(skills_text, styles["BodyText2"]))

    # --- Experience ---
    experience = profile.get("experience", [])
    if experience:
        elements.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["SectionHeading"]))
        elements.append(_section_divider())

        tailored_exp = _tailor_experience_bullets(experience, job)
        for exp in tailored_exp:
            title_line = exp.get("title", "")
            company_name = exp.get("company", "")
            duration = exp.get("duration", "")
            location = exp.get("location", "")

            title_table_data = [[
                Paragraph(f"<b>{title_line}</b>", styles["JobTitle"]),
                Paragraph(f"<i>{duration}</i>", ParagraphStyle(
                    "RightAlign", parent=styles["CompanyLine"], alignment=2
                )),
            ]]
            title_table = Table(title_table_data, colWidths=[4.5 * inch, 2.1 * inch])
            title_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(title_table)

            if company_name:
                company_loc = company_name
                if location:
                    company_loc += f" — {location}"
                elements.append(Paragraph(company_loc, styles["CompanyLine"]))

            for bullet in exp.get("bullets", []):
                all_text_errors.extend(_spell_check_text(bullet))
                elements.append(Paragraph(
                    f"• {bullet}",
                    styles["BulletPoint"],
                ))
            elements.append(Spacer(1, 4))

    # --- Education ---
    education = profile.get("education", [])
    if education:
        elements.append(Paragraph("EDUCATION", styles["SectionHeading"]))
        elements.append(_section_divider())
        for edu in education:
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            year = edu.get("year", "")
            gpa = edu.get("gpa", "")

            edu_table_data = [[
                Paragraph(f"<b>{degree}</b>", styles["JobTitle"]),
                Paragraph(f"<i>{year}</i>", ParagraphStyle(
                    "RightAlign2", parent=styles["CompanyLine"], alignment=2
                )),
            ]]
            edu_table = Table(edu_table_data, colWidths=[4.5 * inch, 2.1 * inch])
            edu_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(edu_table)
            inst_line = institution
            if gpa:
                inst_line += f" | GPA: {gpa}"
            elements.append(Paragraph(inst_line, styles["CompanyLine"]))
            elements.append(Spacer(1, 3))

    # --- Certifications ---
    certs = profile.get("certifications", [])
    if certs:
        elements.append(Paragraph("CERTIFICATIONS", styles["SectionHeading"]))
        elements.append(_section_divider())
        for cert in certs:
            if isinstance(cert, dict):
                cert_text = f"• {cert.get('name', '')} — {cert.get('issuer', '')} ({cert.get('year', '')})"
            else:
                cert_text = f"• {cert}"
            elements.append(Paragraph(cert_text, styles["BulletPoint"]))

    # --- Projects ---
    projects = profile.get("projects", [])
    if projects:
        elements.append(Paragraph("KEY PROJECTS", styles["SectionHeading"]))
        elements.append(_section_divider())
        for proj in projects:
            proj_name = proj.get("name", "")
            proj_tech = proj.get("technologies", "")
            elements.append(Paragraph(f"<b>{proj_name}</b>", styles["JobTitle"]))
            if proj_tech:
                elements.append(Paragraph(f"Technologies: {proj_tech}", styles["CompanyLine"]))
            for bullet in proj.get("bullets", []):
                all_text_errors.extend(_spell_check_text(bullet))
                elements.append(Paragraph(f"• {bullet}", styles["BulletPoint"]))
            elements.append(Spacer(1, 3))

    doc.build(elements)

    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())

    return {
        "filepath": filepath,
        "filename": filename,
        "errors": all_text_errors,
        "error_free": len(all_text_errors) == 0,
        "page_count": _count_pages(buffer),
    }


def _count_pages(buffer: BytesIO) -> int:
    content = buffer.getvalue()
    return content.count(b"/Type /Page") - content.count(b"/Type /Pages")


def generate_cover_letter(profile: dict, job: dict) -> str:
    name = profile.get("name", "")
    email = profile.get("email", "")
    phone = profile.get("phone", "")
    exp_years = profile.get("experience_years", 2.6)
    skills = profile.get("skills", [])
    if skills and isinstance(skills[0], dict):
        flat_skills = []
        for cat in skills:
            flat_skills.extend(cat.get("items", []))
        skills = flat_skills

    job_title = job.get("title", "Software Engineer")
    company = job.get("company", "your company")
    required_skills = job.get("required_skills", [])

    matched = [s for s in required_skills if s.lower() in [sk.lower() for sk in skills]]
    matched_str = ", ".join(matched[:4]) if matched else ", ".join(skills[:4])

    today = datetime.now().strftime("%B %d, %Y")

    return f"""
{name}
{email} | {phone}
{today}

Hiring Manager
{company}

Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With {exp_years}+ years of hands-on experience in software testing, automation, and quality assurance, I am confident in my ability to make meaningful contributions to your team.

My technical expertise spans {matched_str}, which directly aligns with the requirements outlined in your job description. Throughout my career, I have demonstrated a commitment to delivering high-quality software through comprehensive testing strategies, efficient automation frameworks, and meticulous attention to detail.

Key highlights of my qualifications include:
• Proven experience in designing and executing test plans, test cases, and automated test scripts
• Strong proficiency in both manual and automated testing methodologies
• Track record of identifying critical defects early in the development lifecycle, reducing production issues
• Excellent collaboration skills, working effectively with cross-functional development teams

I am particularly drawn to {company}'s commitment to innovation and quality. I am eager to bring my testing expertise and problem-solving abilities to your team and contribute to the continued success of your products.

I would welcome the opportunity to discuss how my skills and experience align with your needs. Thank you for considering my application.

Sincerely,
{name}
""".strip()
