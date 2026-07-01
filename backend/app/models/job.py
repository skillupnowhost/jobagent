from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(500), unique=True, index=True)
    title = Column(String(500), nullable=False)
    company = Column(String(300), nullable=False)
    location = Column(String(300))
    job_type = Column(String(100))  # full-time, part-time, contract
    remote = Column(Boolean, default=False)

    description = Column(Text)
    requirements = Column(Text)
    required_skills = Column(JSON, default=list)
    nice_to_have_skills = Column(JSON, default=list)
    experience_min = Column(Float)
    experience_max = Column(Float)

    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String(10), default="INR")
    salary_disclosed = Column(Boolean, default=True)

    source = Column(String(100))  # linkedin, glassdoor, indeed, etc.
    source_url = Column(String(1000))
    apply_url = Column(String(1000))

    company_size = Column(String(100))
    company_type = Column(String(100))  # MNC, startup, etc.
    is_mnc = Column(Boolean, default=False)

    match_score = Column(Float, default=0.0)
    skill_match_details = Column(JSON, default=dict)

    posted_date = Column(DateTime)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    applications = relationship("Application", back_populates="job")
