from collections import Counter
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.skill import SkillProgress, SkillDemand
from app.models.application import Application
from app.models.job import Job


LEARNING_RESOURCES = {
    "selenium": {
        "beginner": [
            {"title": "Selenium WebDriver with Python - Complete Course", "type": "course", "platform": "Udemy", "url": "https://udemy.com"},
            {"title": "Selenium Documentation", "type": "docs", "platform": "Official", "url": "https://selenium.dev/documentation"},
        ],
        "intermediate": [
            {"title": "Advanced Selenium Framework Design", "type": "course", "platform": "Udemy", "url": "https://udemy.com"},
            {"title": "Page Object Model Best Practices", "type": "article", "platform": "Medium", "url": "https://medium.com"},
        ],
        "advanced": [
            {"title": "Selenium Grid & Parallel Execution", "type": "course", "platform": "Pluralsight", "url": "https://pluralsight.com"},
        ],
    },
    "cypress": {
        "beginner": [
            {"title": "Cypress End-to-End Testing", "type": "course", "platform": "Cypress.io", "url": "https://learn.cypress.io"},
            {"title": "Cypress Documentation", "type": "docs", "platform": "Official", "url": "https://docs.cypress.io"},
        ],
        "intermediate": [
            {"title": "Advanced Cypress Testing Patterns", "type": "course", "platform": "Udemy", "url": "https://udemy.com"},
        ],
    },
    "playwright": {
        "beginner": [
            {"title": "Playwright Getting Started", "type": "docs", "platform": "Official", "url": "https://playwright.dev/docs/intro"},
            {"title": "Playwright Test Automation", "type": "course", "platform": "YouTube", "url": "https://youtube.com"},
        ],
    },
    "api testing": {
        "beginner": [
            {"title": "Postman - The Complete Guide", "type": "course", "platform": "Udemy", "url": "https://udemy.com"},
            {"title": "REST API Testing with Python", "type": "course", "platform": "Udemy", "url": "https://udemy.com"},
        ],
        "intermediate": [
            {"title": "REST Assured API Automation", "type": "course", "platform": "Udemy", "url": "https://udemy.com"},
        ],
    },
    "python": {
        "beginner": [
            {"title": "Python for Testers", "type": "course", "platform": "Udemy", "url": "https://udemy.com"},
        ],
        "intermediate": [
            {"title": "Python Advanced Concepts", "type": "course", "platform": "Coursera", "url": "https://coursera.org"},
        ],
    },
    "java": {
        "beginner": [
            {"title": "Java Programming Masterclass", "type": "course", "platform": "Udemy", "url": "https://udemy.com"},
        ],
    },
    "ci/cd": {
        "beginner": [
            {"title": "Jenkins Pipeline Tutorial", "type": "course", "platform": "YouTube", "url": "https://youtube.com"},
            {"title": "GitHub Actions Documentation", "type": "docs", "platform": "GitHub", "url": "https://docs.github.com/en/actions"},
        ],
    },
    "docker": {
        "beginner": [
            {"title": "Docker for Beginners", "type": "course", "platform": "Docker.com", "url": "https://docker.com"},
        ],
    },
    "kubernetes": {
        "beginner": [
            {"title": "Kubernetes Basics", "type": "course", "platform": "Kubernetes.io", "url": "https://kubernetes.io/docs/tutorials"},
        ],
    },
    "performance testing": {
        "beginner": [
            {"title": "JMeter for Beginners", "type": "course", "platform": "Udemy", "url": "https://udemy.com"},
            {"title": "Gatling Load Testing", "type": "docs", "platform": "Official", "url": "https://gatling.io/docs"},
        ],
    },
    "sql": {
        "beginner": [
            {"title": "SQL for Data Analysis", "type": "course", "platform": "Coursera", "url": "https://coursera.org"},
        ],
    },
    "appium": {
        "beginner": [
            {"title": "Appium Mobile Testing", "type": "course", "platform": "Udemy", "url": "https://udemy.com"},
        ],
    },
}

SKILL_CATEGORIES = {
    "selenium": "automation_framework",
    "cypress": "automation_framework",
    "playwright": "automation_framework",
    "appium": "automation_framework",
    "python": "programming_language",
    "java": "programming_language",
    "javascript": "programming_language",
    "typescript": "programming_language",
    "api testing": "testing_type",
    "performance testing": "testing_type",
    "manual testing": "testing_type",
    "security testing": "testing_type",
    "ci/cd": "devops",
    "docker": "devops",
    "kubernetes": "devops",
    "jenkins": "devops",
    "git": "tool",
    "jira": "tool",
    "postman": "tool",
    "sql": "database",
    "agile": "methodology",
}


class SkillAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def analyze_gaps(self, user_id: int, user_skills: list[str]) -> dict:
        applications = self.db.query(Application).filter(
            Application.user_id == user_id
        ).all()

        all_required = []
        for app in applications:
            if app.skill_gaps:
                all_required.extend(app.skill_gaps)
            job = self.db.query(Job).filter(Job.id == app.job_id).first()
            if job and job.required_skills:
                all_required.extend(job.required_skills)

        demand_counter = Counter(s.lower() for s in all_required)
        user_skills_lower = {s.lower() for s in user_skills}

        gaps = []
        for skill, count in demand_counter.most_common(20):
            if skill not in user_skills_lower:
                severity = "critical" if count > 10 else "high" if count > 5 else "medium" if count > 2 else "low"
                gaps.append({
                    "skill": skill,
                    "demand_count": count,
                    "severity": severity,
                    "category": SKILL_CATEGORIES.get(skill, "other"),
                    "resources": self._get_resources(skill, "beginner"),
                })

        self._update_demand_table(demand_counter)

        return {
            "total_gaps": len(gaps),
            "critical_gaps": [g for g in gaps if g["severity"] == "critical"],
            "high_gaps": [g for g in gaps if g["severity"] == "high"],
            "medium_gaps": [g for g in gaps if g["severity"] == "medium"],
            "low_gaps": [g for g in gaps if g["severity"] == "low"],
            "all_gaps": gaps,
            "learning_path": self._generate_learning_path(gaps[:5]),
        }

    def track_progress(self, user_id: int, skill_name: str,
                       hours: float, level: str = None) -> SkillProgress:
        progress = self.db.query(SkillProgress).filter(
            SkillProgress.user_id == user_id,
            SkillProgress.skill_name == skill_name.lower(),
        ).first()

        if not progress:
            progress = SkillProgress(
                user_id=user_id,
                skill_name=skill_name.lower(),
                category=SKILL_CATEGORIES.get(skill_name.lower(), "other"),
                current_level="beginner",
                target_level="intermediate",
                proficiency_score=0,
            )
            self.db.add(progress)

        progress.hours_invested += hours
        progress.last_studied = datetime.now(timezone.utc)

        if level:
            progress.current_level = level

        if progress.hours_invested >= 100:
            progress.current_level = "advanced"
            progress.proficiency_score = min(100, progress.proficiency_score + 5)
        elif progress.hours_invested >= 40:
            progress.current_level = "intermediate"
            progress.proficiency_score = min(80, progress.proficiency_score + 5)
        else:
            progress.proficiency_score = min(50, progress.hours_invested * 1.25)

        progress.recommended_resources = self._get_resources(
            skill_name.lower(), progress.current_level
        )

        self.db.commit()
        self.db.refresh(progress)
        return progress

    def get_user_progress(self, user_id: int) -> list[dict]:
        progress_list = self.db.query(SkillProgress).filter(
            SkillProgress.user_id == user_id
        ).order_by(SkillProgress.proficiency_score.desc()).all()

        return [
            {
                "skill": p.skill_name,
                "category": p.category,
                "current_level": p.current_level,
                "target_level": p.target_level,
                "proficiency": p.proficiency_score,
                "hours_invested": p.hours_invested,
                "last_studied": p.last_studied.isoformat() if p.last_studied else None,
                "resources": p.recommended_resources or [],
            }
            for p in progress_list
        ]

    def refine_job_targeting(self, user_id: int, user_skills: list[str]) -> dict:
        progress_list = self.db.query(SkillProgress).filter(
            SkillProgress.user_id == user_id,
            SkillProgress.current_level.in_(["intermediate", "advanced"]),
        ).all()

        improved_skills = [p.skill_name for p in progress_list]
        all_skills = list(set([s.lower() for s in user_skills] + improved_skills))

        new_roles = []
        role_skill_map = {
            "SDET": ["python", "java", "selenium", "api testing", "ci/cd"],
            "Automation Architect": ["selenium", "cypress", "playwright", "ci/cd", "docker"],
            "Performance Engineer": ["performance testing", "jmeter", "gatling", "sql"],
            "DevOps QA Engineer": ["ci/cd", "docker", "kubernetes", "jenkins"],
            "Full Stack QA": ["selenium", "api testing", "sql", "python", "javascript"],
        }

        for role, required in role_skill_map.items():
            match_count = sum(1 for s in required if s in all_skills)
            if match_count >= len(required) * 0.6:
                new_roles.append({
                    "role": role,
                    "readiness": round(match_count / len(required) * 100, 1),
                    "missing": [s for s in required if s not in all_skills],
                })

        return {
            "current_skills": all_skills,
            "recommended_roles": sorted(new_roles, key=lambda x: x["readiness"], reverse=True),
            "upskill_impact": self._calculate_upskill_impact(user_id),
        }

    def _get_resources(self, skill: str, level: str) -> list[dict]:
        skill_lower = skill.lower()
        if skill_lower in LEARNING_RESOURCES:
            return LEARNING_RESOURCES[skill_lower].get(level, [])
        return []

    def _generate_learning_path(self, top_gaps: list[dict]) -> list[dict]:
        path = []
        for i, gap in enumerate(top_gaps):
            path.append({
                "order": i + 1,
                "skill": gap["skill"],
                "target_level": "intermediate",
                "estimated_hours": 30 if gap["severity"] == "critical" else 20,
                "resources": gap.get("resources", []),
                "milestones": [
                    f"Complete introductory course on {gap['skill']}",
                    f"Build a small project using {gap['skill']}",
                    f"Apply {gap['skill']} in a real testing scenario",
                ],
            })
        return path

    def _calculate_upskill_impact(self, user_id: int) -> dict:
        recent_apps = self.db.query(Application).filter(
            Application.user_id == user_id
        ).order_by(Application.created_at.desc()).limit(50).all()

        if not recent_apps:
            return {"average_score_before": 0, "potential_improvement": 0}

        avg_score = sum(a.match_score for a in recent_apps) / len(recent_apps)
        return {
            "current_average_score": round(avg_score, 2),
            "potential_improvement": round(min(100, avg_score * 1.2), 2),
            "applications_analyzed": len(recent_apps),
        }

    def _update_demand_table(self, demand_counter: Counter):
        for skill, count in demand_counter.most_common(50):
            demand = self.db.query(SkillDemand).filter(
                SkillDemand.skill_name == skill
            ).first()
            if demand:
                demand.demand_count = count
                demand.last_updated = datetime.now(timezone.utc)
            else:
                demand = SkillDemand(
                    skill_name=skill,
                    demand_count=count,
                    trend="stable",
                )
                self.db.add(demand)
        self.db.commit()
