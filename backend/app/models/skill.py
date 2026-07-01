from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class SkillProgress(Base):
    __tablename__ = "skill_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)

    skill_name = Column(String(200), nullable=False)
    category = Column(String(100))  # technical, soft_skill, tool, framework
    current_level = Column(String(50))  # beginner, intermediate, advanced
    target_level = Column(String(50))
    proficiency_score = Column(Float, default=0.0)  # 0-100

    demand_score = Column(Float, default=0.0)  # how in-demand this skill is
    gap_severity = Column(String(50))  # low, medium, high, critical

    recommended_resources = Column(JSON, default=list)
    learning_path = Column(JSON, default=list)
    milestones = Column(JSON, default=list)

    hours_invested = Column(Float, default=0.0)
    last_studied = Column(DateTime)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("UserProfile", back_populates="skill_progress")


class SkillDemand(Base):
    __tablename__ = "skill_demands"

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(200), nullable=False, unique=True)
    demand_count = Column(Integer, default=0)
    avg_salary_association = Column(Float, default=0.0)
    trend = Column(String(50))  # rising, stable, declining
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_date = Column(DateTime, nullable=False)
    jobs_found = Column(Integer, default=0)
    applications_sent = Column(Integer, default=0)
    responses_received = Column(Integer, default=0)
    interviews_scheduled = Column(Integer, default=0)
    top_matches = Column(JSON, default=list)
    skill_gaps_identified = Column(JSON, default=list)
    summary = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
