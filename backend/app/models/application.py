from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    status = Column(String(50), default="pending")
    # pending, resume_generated, applied, email_sent, follow_up_sent,
    # interview_scheduled, rejected, offer_received

    resume_path = Column(String(1000))
    cover_letter_path = Column(String(1000))
    resume_version = Column(Text)
    cover_letter_text = Column(Text)

    applied_via = Column(String(100))  # direct, email, portal
    applied_at = Column(DateTime)
    follow_up_dates = Column(JSON, default=list)
    next_follow_up = Column(DateTime)

    match_score = Column(Float, default=0.0)
    skill_gaps = Column(JSON, default=list)
    recommended_learning = Column(JSON, default=list)

    errors_detected = Column(JSON, default=list)
    error_free = Column(Boolean, default=True)

    notes = Column(Text)
    response_received = Column(Boolean, default=False)
    response_text = Column(Text)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("UserProfile", back_populates="applications")
    job = relationship("Job", back_populates="applications")


class ApplicationLog(Base):
    __tablename__ = "application_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    action = Column(String(200), nullable=False)
    details = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
