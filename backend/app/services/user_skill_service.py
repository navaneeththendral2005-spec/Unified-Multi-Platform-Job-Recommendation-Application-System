from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.resume import Resume
from app.models.user_profile import UserProfile
from app.models.user_skill import UserSkill
from app.services.skill_service import assign_skills_to_user


# ============================================================
# SAVE USER SKILLS
# ============================================================

def save_user_skills(
    db: Session,
    user_id: int,
    skills: list[str],
    resume_id: int | None = None,
    source: str = "resume",
) -> list[UserSkill]:
    """
    Save skills for a user through the central Skill Registry.

    Parameters
    ----------
    user_id:
        ID of the user.

    skills:
        Skill names extracted from the resume or supplied manually.

    resume_id:
        ID of the resume that produced these skills.
        Required for resume-derived skills when available.

    source:
        Origin of the skills, e.g.:
        - "resume"
        - "manual"
        - "profile"
        - "legacy"

    The Skill Service is responsible for:
    - normalization
    - alias resolution
    - canonical skill lookup
    - skill creation
    - duplicate prevention
    - provenance-aware UserSkill creation
    """

    if not skills:
        return []

    # --------------------------------------------------------
    # CLEAN INCOMING SKILLS
    # --------------------------------------------------------

    cleaned_skills: list[str] = []

    for skill in skills:

        if not skill:
            continue

        cleaned_skill = skill.strip()

        if not cleaned_skill:
            continue

        cleaned_skills.append(cleaned_skill)

    if not cleaned_skills:
        return []

    # --------------------------------------------------------
    # ASSIGN THROUGH CENTRAL SKILL REGISTRY
    # --------------------------------------------------------

    saved_skills = assign_skills_to_user(
        db=db,
        user_id=user_id,
        skill_names=cleaned_skills,
        source=source,
        resume_id=resume_id,
    )

    # --------------------------------------------------------
    # REFRESH DATABASE OBJECTS
    # --------------------------------------------------------

    for skill in saved_skills:
        db.refresh(skill)

    return saved_skills


# ============================================================
# GET USER SKILLS
# ============================================================

def get_user_skills(
    db: Session,
    user_id: int,
) -> list[UserSkill]:
    """
    Get all skills belonging to a user.

    This intentionally includes historical resume skills.

    Use sync_skills_to_profile() when the application needs
    the user's CURRENT profile skill set.
    """

    return (
        db.query(UserSkill)
        .options(
            joinedload(UserSkill.skill)
        )
        .filter(
            UserSkill.user_id == user_id
        )
        .order_by(
            UserSkill.skill_name
        )
        .all()
    )


# ============================================================
# GET ACTIVE RESUME SKILLS
# ============================================================

def get_active_resume_skills(
    db: Session,
    user_id: int,
) -> list[UserSkill]:
    """
    Return only skills belonging to the user's active resume.

    Historical resume skills are intentionally excluded.
    """

    active_resume = (
        db.query(Resume)
        .filter(
            Resume.user_id == user_id,
            Resume.is_active.is_(True),
        )
        .first()
    )

    if not active_resume:
        return []

    return (
        db.query(UserSkill)
        .options(
            joinedload(UserSkill.skill)
        )
        .filter(
            UserSkill.user_id == user_id,
            UserSkill.resume_id == active_resume.id,
        )
        .order_by(
            UserSkill.skill_name
        )
        .all()
    )


# ============================================================
# SYNC SKILLS TO USER PROFILE
# ============================================================

def sync_skills_to_profile(
    db: Session,
    user_id: int,
) -> UserProfile | None:
    """
    Synchronize the legacy UserProfile.skills field with the
    user's CURRENT skill state.

    Source of truth:

        1. Skills belonging to the active resume
        2. Skills without resume provenance
           (manual/profile/legacy compatibility records)

    Historical skills belonging to inactive resumes are excluded.

    The Skill Registry / UserSkill architecture remains the
    preferred source of truth. UserProfile.skills exists for
    backward compatibility with older application components.

    This function intentionally does NOT commit.

    The caller owns the transaction.
    """

    # --------------------------------------------------------
    # GET USER PROFILE
    # --------------------------------------------------------

    profile = (
        db.query(UserProfile)
        .filter(
            UserProfile.user_id == user_id
        )
        .first()
    )

    if not profile:
        return None

    # --------------------------------------------------------
    # FIND ACTIVE RESUME
    # --------------------------------------------------------

    active_resume = (
        db.query(Resume)
        .filter(
            Resume.user_id == user_id,
            Resume.is_active.is_(True),
        )
        .first()
    )

    # --------------------------------------------------------
    # BUILD CURRENT SKILL QUERY
    # --------------------------------------------------------
    #
    # Include:
    #
    #   A. Skills from the active resume
    #
    #   B. Skills with no resume provenance
    #      (manual/profile/legacy compatibility)
    #
    # Exclude:
    #
    #   Skills belonging to inactive/older resumes.
    #
    # --------------------------------------------------------

    current_skill_query = (
        db.query(UserSkill)
        .options(
            joinedload(UserSkill.skill)
        )
        .filter(
            UserSkill.user_id == user_id
        )
    )

    if active_resume:
        current_skill_query = current_skill_query.filter(
            or_(
                UserSkill.resume_id == active_resume.id,
                UserSkill.resume_id.is_(None),
            )
        )
    else:
        # No active resume:
        # only profile-level / legacy skills remain relevant.
        current_skill_query = current_skill_query.filter(
            UserSkill.resume_id.is_(None)
        )

    current_user_skills = (
        current_skill_query
        .order_by(
            UserSkill.skill_name
        )
        .all()
    )

    # --------------------------------------------------------
    # EXTRACT CANONICAL SKILL NAMES
    # --------------------------------------------------------

    skill_names: set[str] = set()

    for user_skill in current_user_skills:

        # ----------------------------------------------------
        # PREFERRED SOURCE:
        # CANONICAL SKILL REGISTRY
        # ----------------------------------------------------

        if user_skill.skill:
            skill_names.add(
                user_skill.skill.name
            )

        # ----------------------------------------------------
        # LEGACY FALLBACK
        # ----------------------------------------------------

        elif user_skill.skill_name:
            skill_names.add(
                user_skill.skill_name.strip()
            )

    # --------------------------------------------------------
    # SORT FOR DETERMINISTIC PROFILE VALUE
    # --------------------------------------------------------

    sorted_skill_names = sorted(
        skill_names,
        key=str.lower,
    )

    # --------------------------------------------------------
    # UPDATE LEGACY PROFILE FIELD
    # --------------------------------------------------------

    profile.skills = ", ".join(
        sorted_skill_names
    )

    # --------------------------------------------------------
    # FLUSH ONLY
    # --------------------------------------------------------
    #
    # Do not commit here.
    #
    # The upload/profile operation owns the transaction.
    #
    # --------------------------------------------------------

    db.flush()

    db.refresh(profile)

    return profile