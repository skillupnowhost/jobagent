from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.application import Application, ApplicationLog
from app.models.job import Job
from app.models.user import UserProfile
from app.models.skill import DailyReport


class ApplicationTracker:
    def __init__(self, db: Session):
        self.db = db

    def create_application(self, user_id: int, job_id: int, match_score: float,
                           skill_gaps: list, resume_path: str = None,
                           cover_letter_text: str = None) -> Application:
        existing = self.db.query(Application).filter(
            Application.user_id == user_id,
            Application.job_id == job_id
        ).first()
        if existing:
            return existing

        app = Application(
            user_id=user_id,
            job_id=job_id,
            match_score=match_score,
            skill_gaps=skill_gaps,
            resume_path=resume_path,
            cover_letter_text=cover_letter_text,
            status="pending",
        )
        self.db.add(app)
        self.db.commit()
        self.db.refresh(app)
        self._log(app.id, "created", "Application created")
        return app

    def update_status(self, application_id: int, status: str, notes: str = None) -> Application:
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return None
        old_status = app.status
        app.status = status
        if notes:
            app.notes = notes
        if status == "applied":
            app.applied_at = datetime.now(timezone.utc)
            app.next_follow_up = datetime.now(timezone.utc) + timedelta(days=3)
        self.db.commit()
        self._log(application_id, "status_changed", f"{old_status} → {status}")
        return app

    def mark_applied(self, application_id: int, applied_via: str = "direct",
                     resume_path: str = None) -> Application:
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return None
        app.status = "applied"
        app.applied_via = applied_via
        app.applied_at = datetime.now(timezone.utc)
        app.next_follow_up = datetime.now(timezone.utc) + timedelta(days=3)
        if resume_path:
            app.resume_path = resume_path
        self.db.commit()
        self._log(application_id, "applied", f"Applied via {applied_via}")
        return app

    def get_pending_follow_ups(self) -> list[Application]:
        now = datetime.now(timezone.utc)
        return self.db.query(Application).filter(
            Application.next_follow_up <= now,
            Application.status.in_(["applied", "email_sent", "follow_up_sent"]),
            Application.response_received == False,
        ).all()

    def schedule_follow_up(self, application_id: int, days: int = 3):
        app = self.db.query(Application).filter(Application.id == application_id).first()
        if app:
            follow_up_date = datetime.now(timezone.utc) + timedelta(days=days)
            app.next_follow_up = follow_up_date
            follow_ups = app.follow_up_dates or []
            follow_ups.append(follow_up_date.isoformat())
            app.follow_up_dates = follow_ups
            self.db.commit()

    def get_all_applications(self, user_id: int, status: str = None,
                             limit: int = 100, offset: int = 0) -> list[Application]:
        query = self.db.query(Application).filter(Application.user_id == user_id)
        if status:
            query = query.filter(Application.status == status)
        return query.order_by(Application.created_at.desc()).offset(offset).limit(limit).all()

    def get_statistics(self, user_id: int) -> dict:
        total = self.db.query(Application).filter(Application.user_id == user_id).count()
        applied = self.db.query(Application).filter(
            Application.user_id == user_id,
            Application.status == "applied"
        ).count()
        interviews = self.db.query(Application).filter(
            Application.user_id == user_id,
            Application.status == "interview_scheduled"
        ).count()
        offers = self.db.query(Application).filter(
            Application.user_id == user_id,
            Application.status == "offer_received"
        ).count()
        rejected = self.db.query(Application).filter(
            Application.user_id == user_id,
            Application.status == "rejected"
        ).count()
        pending = self.db.query(Application).filter(
            Application.user_id == user_id,
            Application.status == "pending"
        ).count()

        avg_score = self.db.query(func.avg(Application.match_score)).filter(
            Application.user_id == user_id
        ).scalar() or 0

        today = datetime.now(timezone.utc).date()
        today_count = self.db.query(Application).filter(
            Application.user_id == user_id,
            func.date(Application.created_at) == today,
        ).count()

        return {
            "total": total,
            "applied": applied,
            "interviews": interviews,
            "offers": offers,
            "rejected": rejected,
            "pending": pending,
            "today_applications": today_count,
            "average_match_score": round(avg_score, 2),
            "response_rate": round((interviews + offers + rejected) / max(applied, 1) * 100, 1),
        }

    def generate_daily_report(self, user_id: int) -> dict:
        stats = self.get_statistics(user_id)
        today = datetime.now(timezone.utc)

        top_matches = self.db.query(Application).join(Job).filter(
            Application.user_id == user_id,
            func.date(Application.created_at) == today.date(),
        ).order_by(Application.match_score.desc()).limit(5).all()

        top_match_details = []
        for app in top_matches:
            top_match_details.append({
                "job_title": app.job.title,
                "company": app.job.company,
                "match_score": app.match_score,
                "status": app.status,
            })

        all_gaps = []
        recent_apps = self.db.query(Application).filter(
            Application.user_id == user_id,
            Application.skill_gaps != None,
        ).order_by(Application.created_at.desc()).limit(20).all()
        for app in recent_apps:
            if app.skill_gaps:
                all_gaps.extend(app.skill_gaps)

        gap_counts = {}
        for g in all_gaps:
            gap_counts[g] = gap_counts.get(g, 0) + 1
        top_gaps = sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        report = DailyReport(
            report_date=today,
            jobs_found=stats["today_applications"],
            applications_sent=stats["applied"],
            responses_received=stats["interviews"] + stats["offers"],
            interviews_scheduled=stats["interviews"],
            top_matches=top_match_details,
            skill_gaps_identified=[g for g, _ in top_gaps],
            summary=self._build_summary(stats, top_gaps),
        )
        self.db.add(report)
        self.db.commit()

        return {
            "date": today.isoformat(),
            "statistics": stats,
            "top_matches": top_match_details,
            "top_skill_gaps": [{"skill": g, "frequency": c} for g, c in top_gaps],
            "summary": report.summary,
        }

    def _build_summary(self, stats: dict, top_gaps: list) -> str:
        lines = [
            f"Daily Report - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            f"Total Applications: {stats['total']} | Applied Today: {stats['today_applications']}",
            f"Interviews: {stats['interviews']} | Offers: {stats['offers']}",
            f"Average Match Score: {stats['average_match_score']}%",
            f"Response Rate: {stats['response_rate']}%",
        ]
        if top_gaps:
            lines.append(f"Top Skills to Learn: {', '.join(g for g, _ in top_gaps[:5])}")
        return "\n".join(lines)

    def _log(self, application_id: int, action: str, details: str):
        log = ApplicationLog(
            application_id=application_id,
            action=action,
            details=details,
        )
        self.db.add(log)
        self.db.commit()
