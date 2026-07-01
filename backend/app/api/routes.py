from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.models.user import UserProfile
from app.models.job import Job
from app.models.application import Application, ApplicationLog
from app.models.skill import SkillProgress, DailyReport
from app.services.resume_builder import generate_resume_pdf, generate_cover_letter
from app.services.job_search import JobSearchAggregator, get_search_queries_for_profile
from app.services.job_matcher import calculate_match_score, should_apply
from app.services.application_tracker import ApplicationTracker
from app.services.skill_analyzer import SkillAnalyzer
from app.services.email_service import EmailService
from app.services.scheduler import job_search_cycle

router = APIRouter()


# ── Pydantic Schemas ──

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


# ── Profile Routes ──

@router.get("/profile")
def get_profile(db: Session = Depends(get_db)):
    user = db.query(UserProfile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found. Please create one.")
    return user


@router.post("/profile")
def create_or_update_profile(data: ProfileCreate, db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.email == data.email).first()
    if user:
        for key, value in data.model_dump().items():
            setattr(user, key, value)
    else:
        user = UserProfile(**data.model_dump())
        db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Profile saved", "user_id": user.id}


# ── Resume Routes ──

@router.post("/resume/generate")
def generate_resume(job_id: int = None, db: Session = Depends(get_db)):
    user = db.query(UserProfile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile = _user_to_dict(user)
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
def download_resume(filename: str):
    import os
    resumes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resumes")
    filepath = os.path.join(resumes_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(filepath, media_type="application/pdf", filename=filename)


@router.post("/resume/cover-letter")
def generate_cover_letter_endpoint(job_id: int, db: Session = Depends(get_db)):
    user = db.query(UserProfile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = _user_to_dict(user)
    job_data = _job_to_dict(job)
    letter = generate_cover_letter(profile, job_data)
    return {"cover_letter": letter}


# ── Job Search Routes ──

@router.get("/jobs/search")
async def search_jobs(
    query: str = "QA Engineer",
    location: str = "India",
    db: Session = Depends(get_db),
):
    searcher = JobSearchAggregator()
    jobs = await searcher.search_all(query, location)

    user = db.query(UserProfile).first()
    if user:
        profile = _user_to_dict(user)
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
async def trigger_search(background_tasks: BackgroundTasks):
    background_tasks.add_task(job_search_cycle)
    return {"message": "Job search triggered in background"}


# ── Application Routes ──

@router.get("/applications")
def list_applications(
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    user = db.query(UserProfile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    tracker = ApplicationTracker(db)
    apps = tracker.get_all_applications(user.id, status, limit, offset)

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
):
    tracker = ApplicationTracker(db)
    app = tracker.update_status(app_id, data.status, data.notes)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Status updated", "status": app.status}


@router.get("/applications/stats")
def get_application_stats(db: Session = Depends(get_db)):
    user = db.query(UserProfile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    tracker = ApplicationTracker(db)
    return tracker.get_statistics(user.id)


@router.get("/applications/{app_id}/logs")
def get_application_logs(app_id: int, db: Session = Depends(get_db)):
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
def get_skill_gaps(db: Session = Depends(get_db)):
    user = db.query(UserProfile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    user_skills = user.skills or []
    if user_skills and isinstance(user_skills[0], dict):
        flat = []
        for cat in user_skills:
            flat.extend(cat.get("items", []))
        user_skills = flat

    analyzer = SkillAnalyzer(db)
    return analyzer.analyze_gaps(user.id, user_skills)


@router.post("/skills/progress")
def update_skill_progress(data: SkillUpdate, db: Session = Depends(get_db)):
    user = db.query(UserProfile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    analyzer = SkillAnalyzer(db)
    progress = analyzer.track_progress(user.id, data.skill_name, data.hours, data.level)
    return {
        "skill": progress.skill_name,
        "level": progress.current_level,
        "proficiency": progress.proficiency_score,
        "hours": progress.hours_invested,
    }


@router.get("/skills/progress")
def get_skill_progress(db: Session = Depends(get_db)):
    user = db.query(UserProfile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    analyzer = SkillAnalyzer(db)
    return analyzer.get_user_progress(user.id)


@router.get("/skills/recommendations")
def get_job_targeting(db: Session = Depends(get_db)):
    user = db.query(UserProfile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    user_skills = user.skills or []
    if user_skills and isinstance(user_skills[0], dict):
        flat = []
        for cat in user_skills:
            flat.extend(cat.get("items", []))
        user_skills = flat

    analyzer = SkillAnalyzer(db)
    return analyzer.refine_job_targeting(user.id, user_skills)


# ── Report Routes ──

@router.get("/reports/daily")
def get_daily_report(db: Session = Depends(get_db)):
    user = db.query(UserProfile).first()
    if not user:
        raise HTTPException(status_code=404, detail="Profile not found")

    tracker = ApplicationTracker(db)
    return tracker.generate_daily_report(user.id)


@router.get("/reports/history")
def get_report_history(limit: int = 30, db: Session = Depends(get_db)):
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
def get_dashboard_data(db: Session = Depends(get_db)):
    user = db.query(UserProfile).first()
    if not user:
        return {
            "profile_exists": False,
            "message": "Please create your profile to get started",
        }

    tracker = ApplicationTracker(db)
    stats = tracker.get_statistics(user.id)

    recent_apps = db.query(Application).filter(
        Application.user_id == user.id
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
        "user_name": user.name,
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
