REQUIRED_PROFILE_SECTIONS = {
    "skills": "Skills",
    "experience": "Work Experience",
    "preferred_roles": "Preferred Roles",
}


def is_profile_complete(profile: dict) -> tuple[bool, list[str]]:
    """Checks whether a profile has enough data for the agent to safely auto-apply.

    Preferences are satisfied by either a preferred role or a preferred location,
    since either alone is enough to target job searches.
    """
    missing = []
    if not profile.get("skills"):
        missing.append("skills")
    if not profile.get("experience"):
        missing.append("experience")
    if not profile.get("preferred_roles") and not profile.get("preferred_locations"):
        missing.append("preferences")
    return (len(missing) == 0, missing)
