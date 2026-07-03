from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Job Application Agent"
    app_env: str = "development"
    frontend_url: str = "http://localhost:5173"

    database_url: str = "sqlite:///./job_agent.db"

    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 10080
    jwt_mfa_pending_expire_minutes: int = 5
    jwt_email_verify_expire_hours: int = 24
    mfa_issuer_name: str = "AI Job Application Agent"

    rate_limit_register: str = "5/hour"
    rate_limit_login: str = "10/minute"
    rate_limit_mfa_verify: str = "5/5minutes"
    rate_limit_resend_verification: str = "3/hour"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = "Sasi@143"
    from_email: str = "sasigod143@gmail.com"
    from_name: str = "AI Job Application Agent"


@lru_cache
def get_settings() -> Settings:
    return Settings()
