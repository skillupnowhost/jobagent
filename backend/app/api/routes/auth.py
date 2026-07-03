from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_verified_user
from app.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    create_email_verify_token,
    create_mfa_pending_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.database import get_db
from app.models.auth import EmailVerificationToken, MFABackupCode, MFASecret
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MFAConfirmRequest,
    MFAConfirmResponse,
    MFADisableRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    MessageResponse,
    RegisterRequest,
    ResendVerificationRequest,
    UserOut,
    VerifyEmailRequest,
)
from app.services import mfa_service
from app.services.email_sender import is_email_configured, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# In-memory failure counter for mfa_pending tokens. Safe only because the
# app runs with a single gunicorn worker (see core/rate_limit.py).
_mfa_attempt_counts: dict[str, int] = {}
MAX_MFA_ATTEMPTS = 5


def _issue_verification_token(user: User, db: Session) -> str:
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used_at.is_(None),
    ).update({"used_at": datetime.now(timezone.utc)})

    raw_token = create_email_verify_token(user.id)
    record = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.jwt_email_verify_expire_hours),
    )
    db.add(record)
    db.commit()
    return raw_token


def _verify_url(raw_token: str) -> str:
    return f"{settings.frontend_url}/verify-email?token={raw_token}"


def _send_verification_email(user: User, raw_token: str) -> None:
    send_verification_email(user.email, user.name, _verify_url(raw_token))


def _dev_verify_url(raw_token: str) -> str | None:
    if settings.app_env == "development" and not is_email_configured():
        return _verify_url(raw_token)
    return None


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_register)
def register(
    request: Request,
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    raw_token = _issue_verification_token(user, db)
    background_tasks.add_task(_send_verification_email, user, raw_token)

    return MessageResponse(
        message="Registration successful. Check your email to verify your account.",
        dev_verify_url=_dev_verify_url(raw_token),
    )


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    try:
        token_payload = decode_token(payload.token, expected_purpose="email_verify")
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired verification link")

    token_hash = hash_token(payload.token)
    record = (
        db.query(EmailVerificationToken)
        .filter(
            EmailVerificationToken.user_id == int(token_payload["sub"]),
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used_at.is_(None),
        )
        .first()
    )
    if record is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired verification link")

    user = db.query(User).filter(User.id == record.user_id).first()
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired verification link")

    user.is_email_verified = True
    record.used_at = datetime.now(timezone.utc)
    db.commit()

    return MessageResponse(message="Email verified successfully. You can now log in.")


@router.post("/resend-verification", response_model=MessageResponse)
@limiter.limit(settings.rate_limit_resend_verification)
def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()
    dev_verify_url = None
    if user is not None and not user.is_email_verified:
        raw_token = _issue_verification_token(user, db)
        background_tasks.add_task(_send_verification_email, user, raw_token)
        dev_verify_url = _dev_verify_url(raw_token)

    # Generic response regardless of whether the account exists or is
    # already verified, to avoid leaking account existence.
    return MessageResponse(
        message="If an account exists and is unverified, a new email has been sent.",
        dev_verify_url=dev_verify_url,
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit(settings.rate_limit_login)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    if not user.is_email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "email_not_verified")

    if user.mfa_enabled:
        return LoginResponse(mfa_required=True, mfa_pending_token=create_mfa_pending_token(user.id))

    return LoginResponse(access_token=create_access_token(user.id))


@router.post("/mfa/verify", response_model=LoginResponse)
@limiter.limit(settings.rate_limit_mfa_verify)
def mfa_verify(request: Request, payload: MFAVerifyRequest, db: Session = Depends(get_db)):
    try:
        token_payload = decode_token(payload.mfa_pending_token, expected_purpose="mfa_pending")
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session, please login again")

    token_key = hash_token(payload.mfa_pending_token)
    if _mfa_attempt_counts.get(token_key, 0) >= MAX_MFA_ATTEMPTS:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Too many attempts, please login again")

    user_id = int(token_payload["sub"])
    secret_row = db.query(MFASecret).filter(MFASecret.user_id == user_id, MFASecret.enabled.is_(True)).first()
    if secret_row is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "MFA is not enabled for this account")

    ok = mfa_service.verify_totp(secret_row.secret, payload.code)

    if not ok:
        code_hash = mfa_service.hash_backup_code(payload.code)
        backup = (
            db.query(MFABackupCode)
            .filter(
                MFABackupCode.user_id == user_id,
                MFABackupCode.code_hash == code_hash,
                MFABackupCode.used_at.is_(None),
            )
            .first()
        )
        if backup is not None:
            backup.used_at = datetime.now(timezone.utc)
            db.commit()
            ok = True

    if not ok:
        _mfa_attempt_counts[token_key] = _mfa_attempt_counts.get(token_key, 0) + 1
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid code")

    _mfa_attempt_counts.pop(token_key, None)
    return LoginResponse(access_token=create_access_token(user_id))


@router.post("/mfa/setup", response_model=MFASetupResponse)
def mfa_setup(current_user: User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    if current_user.mfa_enabled:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "MFA is already enabled")

    db.query(MFASecret).filter(MFASecret.user_id == current_user.id).delete()

    secret = mfa_service.generate_secret()
    db.add(MFASecret(user_id=current_user.id, secret=secret, enabled=False))
    db.commit()

    return MFASetupResponse(
        secret=secret,
        otpauth_url=mfa_service.provisioning_uri(secret, current_user.email),
    )


@router.post("/mfa/confirm", response_model=MFAConfirmResponse)
def mfa_confirm(
    payload: MFAConfirmRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    secret_row = db.query(MFASecret).filter(MFASecret.user_id == current_user.id).first()
    if secret_row is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Call /mfa/setup first")

    if not mfa_service.verify_totp(secret_row.secret, payload.code):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid code")

    secret_row.enabled = True
    secret_row.confirmed_at = datetime.now(timezone.utc)
    current_user.mfa_enabled = True

    db.query(MFABackupCode).filter(MFABackupCode.user_id == current_user.id).delete()
    plain_codes = mfa_service.generate_backup_codes()
    for code in plain_codes:
        db.add(MFABackupCode(user_id=current_user.id, code_hash=mfa_service.hash_backup_code(code)))

    db.commit()
    return MFAConfirmResponse(mfa_enabled=True, backup_codes=plain_codes)


@router.post("/mfa/disable", response_model=MessageResponse)
def mfa_disable(
    payload: MFADisableRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid password")

    secret_row = db.query(MFASecret).filter(MFASecret.user_id == current_user.id).first()
    ok = secret_row is not None and mfa_service.verify_totp(secret_row.secret, payload.code)
    if not ok:
        code_hash = mfa_service.hash_backup_code(payload.code)
        backup = (
            db.query(MFABackupCode)
            .filter(
                MFABackupCode.user_id == current_user.id,
                MFABackupCode.code_hash == code_hash,
                MFABackupCode.used_at.is_(None),
            )
            .first()
        )
        ok = backup is not None

    if not ok:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid code")

    db.query(MFASecret).filter(MFASecret.user_id == current_user.id).delete()
    db.query(MFABackupCode).filter(MFABackupCode.user_id == current_user.id).delete()
    current_user.mfa_enabled = False
    db.commit()

    return MessageResponse(message="MFA disabled.")


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
