from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from jose import JWTError
from app.database import get_db
from app.models.user import UserProfile
from app.models.job import Job
from app.models.application import Application, ApplicationLog
from app.models.skill import SkillProgress, DailyReport
from app.services.resume_builder import generate_resume_pdf, generate_cover_letter
from app.services.resume_parser import parse_resume
from app.services.job_search import JobSearchAggregator, get_search_queries_for_profile
from app.services.job_matcher import calculate_match_score, should_apply
from app.services.application_tracker import ApplicationTracker
from app.services.skill_analyzer import SkillAnalyzer
from app.services.email_service import EmailService
from app.services.scheduler import job_search_cycle
from app.services.profile_utils import is_profile_complete
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserProfile:
    credentials_error = HTTPException(status_code=401, detail="Could not validate credentials")
    if not token:
        raise credentials_error
    try:
        user_id = decode_access_token(token)
    except JWTError:
        raise credentials_error
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise credentials_error
    return user


# ── Pydantic Schemas ──

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileCreate(BaseModel):
    name: str
    email: str
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    professional_summary: str = ""
    experience_years: float = 2.6
    min_salary_lpa: float = 10.0
    skills: list = []
    experience: list = []
    education: list = []
    certifications: list = []
    projects: list = []
    preferred_roles: list = []
    preferred_locations: list = []
    preferred_companies: list = []


class SkillUpdate(BaseModel):
    skill_name: str
    hours: float
    level: str = None


class ApplicationStatusUpdate(BaseModel):
    status: str
    notes: str = None


# ── Auth Routes ──

@router.post("/auth/register", response_model=LoginResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(UserProfile).filter(UserProfile.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    user = UserProfile(name=data.name, email=data.email, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return LoginResponse(access_token=create_access_token(user.id))


@router.post("/auth/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.email == form_data.username).first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    return LoginResponse(access_token=create_access_token(user.id))


@router.get("/auth/me")
def get_me(current_user: UserProfile = Depends(get_current_user)):
    return _user_public_dict(current_user)


# ── Profile Routes ──

@router.get("/profile")
def get_profile(current_user: UserProfile = Depends(get_current_user)):
    return _user_public_dict(current_user)


@router.post("/profile")
def create_or_update_profile(
    data: ProfileCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    if data.email != current_user.email:
        email_taken = db.query(UserProfile).filter(
            UserProfile.email == data.email, UserProfile.id != current_user.id
        ).first()
        if email_taken:
            raise HTTPException(status_code=400, detail="An account with this email already exists")

    for key, value in data.model_dump().items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)

    complete, missing = is_profile_complete(_user_to_dict(current_user))
    if complete:
        background_tasks.add_task(job_search_cycle)

    return {
        "message": "Profile saved",
        "user_id": current_user.id,
        "profile_complete": complete,
        "missing_sections": missing,
        "agent_triggered": complete,
    }


# ── Resume Routes ──

@router.post("/resume/generate")
def generate_resume(
    job_id: int = None,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    profile = _user_to_dict(current_user)
    job_data = None
    if job_id:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job_data = _job_to_dict(job)

    result = generate_resume_pdf(profile, job_data)
    return {
        "filename": result["filename"],
        "filepath": result["filepath"],
        "errors": result["errors"],
        "error_free": result["error_free"],
        "page_count": result["page_count"],
    }


@router.get("/resume/download/{filename}")
def download_resume(filename: str, current_user: UserProfile = Depends(get_current_user)):
    import os
    resumes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resumes")
    filepath = os.path.join(resumes_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(filepath, media_type="application/pdf", filename=filename)


@router.post("/resume/parse")
async def parse_resume_upload(file: UploadFile = File(...)):
    content_type = file.content_type or ""
    if not any(t in content_type for t in ["pdf", "docx", "openxmlformats", "wordprocessingml", "msword", "text"]):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a PDF, DOCX, or TXT file.",
        )
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10 MB allowed.")
    try:
        extracted = parse_resume(file_bytes, content_type)
        return {"success": True, "data": extracted}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {exc}")


@router.post("/resume/cover-letter")
def generate_cover_letter_endpoint(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = _user_to_dict(current_user)
    job_data = _job_to_dict(job)
    letter = generate_cover_letter(profile, job_data)
    return {"cover_letter": letter}


# ── Job Search Routes ──

@router.get("/jobs/search")
async def search_jobs(
    query: str = "QA Engineer",
    location: str = "India",
    current_user: UserProfile = Depends(get_current_user),
):
    searcher = JobSearchAggregator()
    jobs = await searcher.search_all(query, location)

    profile = _user_to_dict(current_user)
    for job_data in jobs:
        match = calculate_match_score(profile, job_data)
        job_data["match_score"] = match["total_score"]
        job_data["match_details"] = match

    jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return {"count": len(jobs), "jobs": jobs}


@router.get("/jobs")
def list_jobs(
    min_score: float = 0,
    source: str = None,
    is_mnc: bool = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    query = db.query(Job).filter(Job.is_active == True)
    if min_score > 0:
        query = query.filter(Job.match_score >= min_score)
    if source:
        query = query.filter(Job.source == source)
    if is_mnc is not None:
        query = query.filter(Job.is_mnc == is_mnc)

    total = query.count()
    jobs = query.order_by(Job.match_score.desc()).offset(offset).limit(limit).all()
    return {"total": total, "jobs": jobs}


@router.post("/jobs/trigger-search")
async def trigger_search(
    background_tasks: BackgroundTasks,
    current_user: UserProfile = Depends(get_current_user),
):
    background_tasks.add_task(job_search_cycle)
    return {"message": "Job search triggered in background"}


# ── Application Routes ──

@router.get("/applications")
def list_applications(
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    tracker = ApplicationTracker(db)
    apps = tracker.get_all_applications(current_user.id, status, limit, offset)

    result = []
    for app in apps:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        result.append({
            "id": app.id,
            "job_title": job.title if job else "Unknown",
            "company": job.company if job else "Unknown",
            "location": job.location if job else "",
            "status": app.status,
            "match_score": app.match_score,
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            "resume_path": app.resume_path,
            "cover_letter": app.cover_letter_text[:200] if app.cover_letter_text else None,
            "skill_gaps": app.skill_gaps,
            "errors": app.errors_detected,
            "error_free": app.error_free,
            "next_follow_up": app.next_follow_up.isoformat() if app.next_follow_up else None,
            "created_at": app.created_at.isoformat(),
        })

    return {"total": len(result), "applications": result}


@router.put("/applications/{app_id}/status")
def update_application_status(
    app_id: int,
    data: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    owned = db.query(Application).filter(
        Application.id == app_id, Application.user_id == current_user.id
    ).first()
    if not owned:
        raise HTTPException(status_code=404, detail="Application not found")

    tracker = ApplicationTracker(db)
    app = tracker.update_status(app_id, data.status, data.notes)
    return {"message": "Status updated", "status": app.status}


@router.get("/applications/stats")
def get_application_stats(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    tracker = ApplicationTracker(db)
    return tracker.get_statistics(current_user.id)


@router.get("/applications/{app_id}/logs")
def get_application_logs(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    owned = db.query(Application).filter(
        Application.id == app_id, Application.user_id == current_user.id
    ).first()
    if not owned:
        raise HTTPException(status_code=404, detail="Application not found")

    logs = db.query(ApplicationLog).filter(
        ApplicationLog.application_id == app_id
    ).order_by(ApplicationLog.timestamp.desc()).all()
    return [
        {
            "action": log.action,
            "details": log.details,
            "timestamp": log.timestamp.isoformat(),
        }
        for log in logs
    ]


# ── Skill Routes ──

@router.get("/skills/gaps")
def get_skill_gaps(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    user_skills = current_user.skills or []
    if user_skills and isinstance(user_skills[0], dict):
        flat = []
        for cat in user_skills:
            flat.extend(cat.get("items", []))
        user_skills = flat

    analyzer = SkillAnalyzer(db)
    return analyzer.analyze_gaps(current_user.id, user_skills)


@router.post("/skills/progress")
def update_skill_progress(
    data: SkillUpdate,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    analyzer = SkillAnalyzer(db)
    progress = analyzer.track_progress(current_user.id, data.skill_name, data.hours, data.level)
    return {
        "skill": progress.skill_name,
        "level": progress.current_level,
        "proficiency": progress.proficiency_score,
        "hours": progress.hours_invested,
    }


@router.get("/skills/progress")
def get_skill_progress(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    analyzer = SkillAnalyzer(db)
    return analyzer.get_user_progress(current_user.id)


@router.get("/skills/recommendations")
def get_job_targeting(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    user_skills = current_user.skills or []
    if user_skills and isinstance(user_skills[0], dict):
        flat = []
        for cat in user_skills:
            flat.extend(cat.get("items", []))
        user_skills = flat

    analyzer = SkillAnalyzer(db)
    return analyzer.refine_job_targeting(current_user.id, user_skills)


# ── Report Routes ──

@router.get("/reports/daily")
def get_daily_report(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    tracker = ApplicationTracker(db)
    return tracker.generate_daily_report(current_user.id)


@router.get("/reports/history")
def get_report_history(
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    reports = db.query(DailyReport).order_by(
        DailyReport.report_date.desc()
    ).limit(limit).all()
    return [
        {
            "date": r.report_date.isoformat(),
            "jobs_found": r.jobs_found,
            "applications_sent": r.applications_sent,
            "responses_received": r.responses_received,
            "interviews_scheduled": r.interviews_scheduled,
            "summary": r.summary,
        }
        for r in reports
    ]


# ── Dashboard ──

@router.get("/dashboard")
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: UserProfile = Depends(get_current_user),
):
    tracker = ApplicationTracker(db)
    stats = tracker.get_statistics(current_user.id)

    recent_apps = db.query(Application).filter(
        Application.user_id == current_user.id
    ).order_by(Application.created_at.desc()).limit(10).all()

    recent = []
    for app in recent_apps:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        recent.append({
            "id": app.id,
            "job_title": job.title if job else "Unknown",
            "company": job.company if job else "Unknown",
            "status": app.status,
            "match_score": app.match_score,
            "applied_at": app.applied_at.isoformat() if app.applied_at else None,
            "error_free": app.error_free,
        })

    top_jobs = db.query(Job).filter(
        Job.is_active == True,
        Job.match_score >= 40,
    ).order_by(Job.match_score.desc()).limit(5).all()

    return {
        "profile_exists": True,
        "user_name": current_user.name,
        "statistics": stats,
        "recent_applications": recent,
        "top_matching_jobs": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "match_score": j.match_score,
                "is_mnc": j.is_mnc,
                "source": j.source,
            }
            for j in top_jobs
        ],
    }


# ── Helpers ──

def _user_public_dict(user: UserProfile) -> dict:
    """Profile fields safe to return over the API — excludes hashed_password."""
    data = _user_to_dict(user)
    data["id"] = user.id
    data["preferred_companies"] = user.preferred_companies or []
    return data


def _user_to_dict(user: UserProfile) -> dict:
    return {
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "location": user.location,
        "linkedin_url": user.linkedin_url,
        "github_url": user.github_url,
        "portfolio_url": user.portfolio_url,
        "professional_summary": user.professional_summary,
        "experience_years": user.experience_years,
        "min_salary_lpa": user.min_salary_lpa,
        "skills": user.skills or [],
        "experience": user.experience or [],
        "education": user.education or [],
        "certifications": user.certifications or [],
        "projects": user.projects or [],
        "preferred_roles": user.preferred_roles or [],
        "preferred_locations": user.preferred_locations or [],
    }


def _job_to_dict(job: Job) -> dict:
    return {
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "requirements": job.requirements,
        "required_skills": job.required_skills or [],
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "source": job.source,
        "apply_url": job.apply_url,
    }
