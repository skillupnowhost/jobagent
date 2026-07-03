from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    mfa_required: bool = False
    mfa_pending_token: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class MFAVerifyRequest(BaseModel):
    mfa_pending_token: str
    code: str


class MFAConfirmRequest(BaseModel):
    code: str


class MFADisableRequest(BaseModel):
    password: str
    code: str


class MFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str


class MFAConfirmResponse(BaseModel):
    mfa_enabled: bool
    backup_codes: list[str]


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    is_email_verified: bool
    mfa_enabled: bool

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
    dev_verify_url: str | None = None
