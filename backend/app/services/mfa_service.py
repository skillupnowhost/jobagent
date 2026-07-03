import hashlib

import pyotp

from app.config import get_settings
from app.core.security import generate_backup_code

settings = get_settings()


def generate_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(secret: str, account_email: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=account_email, issuer_name=settings.mfa_issuer_name
    )


def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def generate_backup_codes(count: int = 10) -> list[str]:
    return [generate_backup_code() for _ in range(count)]


def hash_backup_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()
