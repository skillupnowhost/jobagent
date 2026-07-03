from fastapi import APIRouter, Depends

from app.api.deps import get_current_verified_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(current_user: User = Depends(get_current_verified_user)):
    next_steps = [
        "Complete your profile",
        "Upload your resume",
    ]
    if not current_user.mfa_enabled:
        next_steps.append("Set up multi-factor authentication")

    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "mfa_enabled": current_user.mfa_enabled,
        },
        "stats": {
            "applications_total": 0,
            "interviews": 0,
            "jobs_matched": 0,
            "profile_completeness": 0,
        },
        "recent_activity": [],
        "next_steps": next_steps,
    }
