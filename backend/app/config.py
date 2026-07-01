import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "AI Job Application Agent"
    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    database_url: str = "sqlite:///./job_agent.db"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    from_name: str = ""

    google_credentials_file: str = "credentials.json"
    google_token_file: str = "token.json"

    rapidapi_key: str = ""
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""

    redis_url: str = "redis://localhost:6379/0"

    user_name: str = ""
    user_email: str = ""
    user_phone: str = ""
    user_location: str = ""
    user_linkedin: str = ""
    user_github: str = ""
    user_experience_years: float = 2.6
    user_min_salary_lpa: float = 10.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
