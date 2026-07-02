import asyncio
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import UserProfile
from app.models.job import Job
from app.models.application import Application
from app.services.job_search import JobSearchAggregator, get_search_queries_for_profile
from app.services.job_matcher import calculate_match_score, should_apply
from app.services.resume_builder import generate_resume_pdf, generate_cover_letter
from app.services.application_tracker import ApplicationTracker
from app.services.skill_analyzer import SkillAnalyzer
from app.services.email_service import EmailService
from app.services.profile_utils import is_profile_complete

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def job_search_cycle():
    logger.info("Starting automated job search cycle...")
    db = SessionLocal()
    try:
        user = db.query(UserProfile).first()
        if not user:
            logger.warning("No user profile found. Skipping job search.")
            return

        profile = _user_to_dict(user)
        complete, missing = is_profile_complete(profile)
        if not complete:
            logger.warning(f"Profile incomplete (missing: {', '.join(missing)}). Skipping auto-apply job search.")
            return

        queries = get_search_queries_for_profile(profile)
        searcher = JobSearchAggregator()

        all_jobs = await searcher.search_by_keywords(queries, user.location or "India")
        logger.info(f"Found {len(all_jobs)} jobs across all sources")

        new_jobs = 0
        applied_count = 0
        tracker = ApplicationTracker(db)

        for job_data in all_jobs:
            existing = db.query(Job).filter(
                Job.external_id == job_data["external_id"]
            ).first()
            if existing:
                continue

            job = Job(
                external_id=job_data["external_id"],
                title=job_data.get("title", ""),
                company=job_data.get("company", ""),
                location=job_data.get("location", ""),
                description=job_data.get("description", ""),
                requirements=str(job_data.get("requirements", "")),
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                salary_disclosed=job_data.get("salary_disclosed", False),
                source=job_data.get("source", ""),
                source_url=job_data.get("source_url", ""),
                apply_url=job_data.get("apply_url", ""),
                remote=job_data.get("remote", False),
                job_type=job_data.get("job_type", "full_time"),
                posted_date=datetime.now(timezone.utc),
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            new_jobs += 1

            match_result = calculate_match_score(profile, job_data)
            job.match_score = match_result["total_score"]
            job.skill_match_details = match_result
            job.required_skills = match_result.get("matched_skills", []) + match_result.get("missing_skills", [])
            job.is_mnc = match_result["is_mnc"]
            db.commit()

            if should_apply(match_result):
                resume_result = generate_resume_pdf(profile, job_data)
                cover_letter = generate_cover_letter(profile, job_data)

                app = tracker.create_application(
                    user_id=user.id,
                    job_id=job.id,
                    match_score=match_result["total_score"],
                    skill_gaps=match_result.get("missing_skills", []),
                    resume_path=resume_result["filepath"],
                    cover_letter_text=cover_letter,
                )

                if resume_result["error_free"]:
                    tracker.mark_applied(app.id, "automated", resume_result["filepath"])
                    applied_count += 1
                else:
                    app.errors_detected = resume_result.get("errors", [])
                    app.error_free = False
                    db.commit()

        logger.info(f"Cycle complete: {new_jobs} new jobs, {applied_count} applications sent")

    except Exception as e:
        logger.error(f"Job search cycle error: {e}", exc_info=True)
    finally:
        db.close()


async def follow_up_cycle():
    logger.info("Starting follow-up cycle...")
    db = SessionLocal()
    try:
        tracker = ApplicationTracker(db)
        pending_follow_ups = tracker.get_pending_follow_ups()

        email_service = EmailService()
        user = db.query(UserProfile).first()
        if not user:
            return

        for app in pending_follow_ups:
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if not job:
                continue

            applied_date = app.applied_at.strftime("%B %d, %Y") if app.applied_at else "recently"
            result = email_service.send_follow_up_email(
                to_email=user.email,
                original_subject=f"Application for {job.title}",
                candidate_name=user.name,
                job_title=job.title,
                company=job.company,
                applied_date=applied_date,
            )

            if result["success"]:
                tracker.update_status(app.id, "follow_up_sent")
                tracker.schedule_follow_up(app.id, days=7)
                logger.info(f"Follow-up sent for {job.title} at {job.company}")

    except Exception as e:
        logger.error(f"Follow-up cycle error: {e}", exc_info=True)
    finally:
        db.close()


async def daily_report_cycle():
    logger.info("Generating daily report...")
    db = SessionLocal()
    try:
        user = db.query(UserProfile).first()
        if not user:
            return

        tracker = ApplicationTracker(db)
        report = tracker.generate_daily_report(user.id)

        analyzer = SkillAnalyzer(db)
        user_skills = user.skills if isinstance(user.skills, list) else []
        if user_skills and isinstance(user_skills[0], dict):
            flat = []
            for cat in user_skills:
                flat.extend(cat.get("items", []))
            user_skills = flat

        gaps = analyzer.analyze_gaps(user.id, user_skills)
        report["skill_analysis"] = gaps

        logger.info(f"Daily report generated: {report['summary']}")

    except Exception as e:
        logger.error(f"Daily report error: {e}", exc_info=True)
    finally:
        db.close()


async def skill_demand_update():
    logger.info("Updating skill demand data...")
    db = SessionLocal()
    try:
        user = db.query(UserProfile).first()
        if not user:
            return

        user_skills = user.skills if isinstance(user.skills, list) else []
        if user_skills and isinstance(user_skills[0], dict):
            flat = []
            for cat in user_skills:
                flat.extend(cat.get("items", []))
            user_skills = flat

        analyzer = SkillAnalyzer(db)
        gaps = analyzer.analyze_gaps(user.id, user_skills)
        refinement = analyzer.refine_job_targeting(user.id, user_skills)

        logger.info(f"Skill demand updated. {gaps['total_gaps']} gaps found. "
                     f"Recommended roles: {[r['role'] for r in refinement['recommended_roles']]}")

    except Exception as e:
        logger.error(f"Skill demand update error: {e}", exc_info=True)
    finally:
        db.close()


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


def start_scheduler():
    scheduler.add_job(
        job_search_cycle,
        CronTrigger(hour="*/4"),
        id="job_search",
        name="Automated Job Search",
        replace_existing=True,
    )

    scheduler.add_job(
        follow_up_cycle,
        CronTrigger(hour=10, minute=0),
        id="follow_up",
        name="Follow-up Emails",
        replace_existing=True,
    )

    scheduler.add_job(
        daily_report_cycle,
        CronTrigger(hour=9, minute=0),
        id="daily_report",
        name="Daily Report",
        replace_existing=True,
    )

    scheduler.add_job(
        skill_demand_update,
        CronTrigger(day_of_week="mon", hour=6),
        id="skill_demand",
        name="Skill Demand Update",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with all jobs configured")
