import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def _create_token(subject: str, purpose: str, expires_delta: timedelta, extra_claims: dict | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "purpose": purpose,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        purpose="access",
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )


def create_mfa_pending_token(user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        purpose="mfa_pending",
        expires_delta=timedelta(minutes=settings.jwt_mfa_pending_expire_minutes),
    )


def create_email_verify_token(user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        purpose="email_verify",
        expires_delta=timedelta(hours=settings.jwt_email_verify_expire_hours),
    )


def decode_token(token: str, expected_purpose: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("invalid_token") from exc
    if payload.get("purpose") != expected_purpose:
        raise ValueError("invalid_token_purpose")
    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_backup_code() -> str:
    return f"{secrets.randbelow(10**10):010d}"
