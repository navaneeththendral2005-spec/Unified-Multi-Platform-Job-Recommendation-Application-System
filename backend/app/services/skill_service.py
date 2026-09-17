import re

from sqlalchemy.orm import Session

from app.models.job_skill import JobSkill
from app.models.skill import Skill
from app.models.skill_alias import SkillAlias
from app.models.user_skill import UserSkill


# ============================================================
# SKILL NORMALIZATION
# ============================================================

def normalize_skill_name(
    skill_name: str
) -> str:
    """
    Normalize a skill name for consistent database lookup.

    Examples:

        " Python "   -> "python"
        "NODE.JS"    -> "node.js"
        "Node JS"    -> "node js"
        "React-JS"   -> "react js"
    """

    if not skill_name:
        return ""

    normalized_name = skill_name.strip().lower()

    # Replace underscores with spaces
    normalized_name = normalized_name.replace(
        "_",
        " "
    )

    # Normalize common separators
    normalized_name = re.sub(
        r"[-/]+",
        " ",
        normalized_name
    )

    # Remove repeated spaces
    normalized_name = re.sub(
        r"\s+",
        " ",
        normalized_name
    )

    return normalized_name.strip()


# ============================================================
# VALIDATE SKILL NAME
# ============================================================

def validate_skill_name(
    skill_name: str
) -> str:
    """
    Validate and clean an incoming skill name.
    """

    if not isinstance(skill_name, str):

        raise ValueError(
            "Skill name must be a string"
        )

    cleaned_name = skill_name.strip()

    if not cleaned_name:

        raise ValueError(
            "Skill name cannot be empty"
        )

    if len(cleaned_name) > 100:

        raise ValueError(
            "Skill name cannot exceed 100 characters"
        )

    return cleaned_name


# ============================================================
# FIND CANONICAL SKILL
# ============================================================

def find_skill_by_canonical_name(
    db: Session,
    skill_name: str
) -> Skill | None:
    """
    Find a canonical skill using its normalized name.
    """

    normalized_name = normalize_skill_name(
        skill_name
    )

    if not normalized_name:
        return None

    return (
        db.query(Skill)
        .filter(
            Skill.normalized_name == normalized_name
        )
        .first()
    )


# ============================================================
# FIND SKILL THROUGH ALIAS
# ============================================================

def find_skill_by_alias(
    db: Session,
    skill_name: str
) -> Skill | None:
    """
    Find a canonical skill through one of its aliases.
    """

    normalized_name = normalize_skill_name(
        skill_name
    )

    if not normalized_name:
        return None

    skill_alias = (
        db.query(SkillAlias)
        .filter(
            SkillAlias.normalized_alias == normalized_name
        )
        .first()
    )

    if skill_alias:
        return skill_alias.skill

    return None


# ============================================================
# FIND SKILL BY NAME OR ALIAS
# ============================================================

def find_skill_by_name_or_alias(
    db: Session,
    skill_name: str
) -> Skill | None:
    """
    Find a skill using either:

    1. Its canonical normalized name
    2. A registered alias
    """

    normalized_name = normalize_skill_name(
        skill_name
    )

    if not normalized_name:
        return None

    # --------------------------------------------------------
    # LOOK FOR CANONICAL SKILL
    # --------------------------------------------------------

    skill = find_skill_by_canonical_name(
        db,
        normalized_name
    )

    if skill:
        return skill

    # --------------------------------------------------------
    # LOOK FOR SKILL ALIAS
    # --------------------------------------------------------

    skill = find_skill_by_alias(
        db,
        normalized_name
    )

    if skill:
        return skill

    return None


# ============================================================
# GET OR CREATE SKILL
# ============================================================

def get_or_create_skill(
    db: Session,
    skill_name: str
) -> Skill:
    """
    Get a canonical skill from the central Skill Registry.

    Processing order:

    1. Validate skill name
    2. Normalize skill name
    3. Search canonical skills
    4. Search registered aliases
    5. Create a new canonical skill if necessary
    """

    cleaned_name = validate_skill_name(
        skill_name
    )

    normalized_name = normalize_skill_name(
        cleaned_name
    )

    # --------------------------------------------------------
    # CHECK EXISTING CANONICAL SKILL OR ALIAS
    # --------------------------------------------------------

    existing_skill = find_skill_by_name_or_alias(
        db,
        cleaned_name
    )

    if existing_skill:
        return existing_skill

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    existing_skill = (
        db.query(Skill)
        .filter(
            Skill.normalized_name == normalized_name
        )
        .first()
    )

    if existing_skill:
        return existing_skill

    # --------------------------------------------------------
    # CREATE NEW CANONICAL SKILL
    # --------------------------------------------------------

    skill = Skill(
        name=cleaned_name,
        normalized_name=normalized_name
    )

    db.add(skill)
    db.flush()

    return skill


# ============================================================
# CREATE SKILL ALIAS
# ============================================================

def create_skill_alias(
    db: Session,
    skill: Skill,
    alias_name: str
) -> SkillAlias:
    """
    Create an alternative name for a canonical skill.

    Safety protections:

    - Alias cannot be empty
    - Alias cannot equal canonical skill name
    - Alias cannot duplicate another alias
    - Alias cannot conflict with another canonical skill
    """

    if not skill:
        raise ValueError(
            "A valid canonical skill is required"
        )

    cleaned_alias = validate_skill_name(
        alias_name
    )

    normalized_alias = normalize_skill_name(
        cleaned_alias
    )

    # --------------------------------------------------------
    # PREVENT ALIAS = CANONICAL NAME
    # --------------------------------------------------------

    if normalized_alias == skill.normalized_name:
        raise ValueError(
            "Alias cannot be the same as "
            "the canonical skill name"
        )

    # --------------------------------------------------------
    # CHECK CANONICAL SKILL CONFLICT
    # --------------------------------------------------------

    canonical_skill_conflict = (
        db.query(Skill)
        .filter(
            Skill.normalized_name == normalized_alias
        )
        .first()
    )

    if canonical_skill_conflict:
        raise ValueError(
            "Alias conflicts with an existing "
            "canonical skill"
        )

    # --------------------------------------------------------
    # CHECK EXISTING ALIAS
    # --------------------------------------------------------

    existing_alias = (
        db.query(SkillAlias)
        .filter(
            SkillAlias.normalized_alias == normalized_alias
        )
        .first()
    )

    if existing_alias:

        # Alias already belongs to the same skill
        if existing_alias.skill_id == skill.id:
            return existing_alias

        # Alias belongs to another skill
        raise ValueError(
            "Alias already belongs to another skill"
        )

    # --------------------------------------------------------
    # CREATE ALIAS
    # --------------------------------------------------------

    skill_alias = SkillAlias(
        alias=cleaned_alias,
        normalized_alias=normalized_alias,
        skill_id=skill.id
    )

    db.add(skill_alias)
    db.flush()

    return skill_alias


# ============================================================
# USER SKILL ASSIGNMENT
# ============================================================

def assign_skill_to_user(
    db: Session,
    user_id: int,
    skill_name: str,
    source: str = "resume",
    resume_id: int | None = None
) -> UserSkill:
    """
    Assign a canonical skill to a user.

    For resume-derived skills, resume_id identifies
    the specific resume that produced the skill.

    Duplicate protection:

    Resume skill:
        user + skill + resume

    Non-resume skill:
        user + skill + source
    """

    skill = get_or_create_skill(
        db,
        skill_name
    )

    # --------------------------------------------------------
    # CHECK EXISTING USER-SKILL RELATIONSHIP
    # --------------------------------------------------------

    existing_query = (
        db.query(UserSkill)
        .filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id == skill.id
        )
    )

    if source == "resume" and resume_id is not None:

        existing_user_skill = (
            existing_query
            .filter(
                UserSkill.resume_id == resume_id
            )
            .first()
        )

    else:

        existing_user_skill = (
            existing_query
            .filter(
                UserSkill.source == source,
                UserSkill.resume_id.is_(None)
            )
            .first()
        )

    # --------------------------------------------------------
    # SKILL ALREADY EXISTS FOR THIS SOURCE
    # --------------------------------------------------------

    if existing_user_skill:
        return existing_user_skill

    # --------------------------------------------------------
    # CREATE USER-SKILL RELATIONSHIP
    # --------------------------------------------------------

    user_skill = UserSkill(
        user_id=user_id,
        skill_id=skill.id,
        skill_name=skill.name,
        source=source,
        resume_id=resume_id
    )

    db.add(user_skill)
    db.flush()

    return user_skill


# ============================================================
# BULK USER SKILL ASSIGNMENT
# ============================================================

def assign_skills_to_user(
    db: Session,
    user_id: int,
    skill_names: list[str],
    source: str = "resume",
    resume_id: int | None = None
) -> list[UserSkill]:
    """
    Assign multiple canonical skills to a user.

    Duplicate incoming skill names are removed before
    assignment.

    For resume-derived skills, resume_id identifies
    the specific resume that produced the skills.
    """

    if not skill_names:
        return []

    user_skills = []

    processed_skills = set()

    for skill_name in skill_names:

        if not skill_name:
            continue

        normalized_name = normalize_skill_name(
            skill_name
        )

        if not normalized_name:
            continue

        # ----------------------------------------------------
        # PREVENT DUPLICATE INPUT PROCESSING
        # ----------------------------------------------------

        if normalized_name in processed_skills:
            continue

        processed_skills.add(
            normalized_name
        )

        # ----------------------------------------------------
        # ASSIGN SKILL
        # ----------------------------------------------------

        user_skill = assign_skill_to_user(
            db=db,
            user_id=user_id,
            skill_name=skill_name,
            source=source,
            resume_id=resume_id
        )

        user_skills.append(
            user_skill
        )

    return user_skills


# ============================================================
# JOB SKILL ASSIGNMENT
# ============================================================

def assign_skill_to_job(
    db: Session,
    job_id: int,
    skill_name: str
) -> JobSkill:
    """
    Assign a canonical skill requirement to a job.

    Aliases automatically resolve to their
    canonical Skill.
    """

    skill = get_or_create_skill(
        db,
        skill_name
    )

    # --------------------------------------------------------
    # CHECK EXISTING JOB-SKILL RELATIONSHIP
    # --------------------------------------------------------

    existing_job_skill = (
        db.query(JobSkill)
        .filter(
            JobSkill.job_id == job_id,
            JobSkill.skill_id == skill.id
        )
        .first()
    )

    if existing_job_skill:
        return existing_job_skill

    # --------------------------------------------------------
    # CREATE JOB-SKILL RELATIONSHIP
    # --------------------------------------------------------

    job_skill = JobSkill(
        job_id=job_id,
        skill_id=skill.id
    )

    db.add(job_skill)
    db.flush()

    return job_skill


# ============================================================
# BULK JOB SKILL ASSIGNMENT
# ============================================================

def assign_skills_to_job(
    db: Session,
    job_id: int,
    skill_names: list[str]
) -> list[JobSkill]:
    """
    Assign multiple canonical skills to a job.

    Duplicate incoming skill names are removed
    before assignment.
    """

    if not skill_names:
        return []

    job_skills = []

    processed_skills = set()

    for skill_name in skill_names:

        if not skill_name:
            continue

        normalized_name = normalize_skill_name(
            skill_name
        )

        if not normalized_name:
            continue

        # ----------------------------------------------------
        # PREVENT DUPLICATE INPUT PROCESSING
        # ----------------------------------------------------

        if normalized_name in processed_skills:
            continue

        processed_skills.add(
            normalized_name
        )

        # ----------------------------------------------------
        # ASSIGN SKILL
        # ----------------------------------------------------

        job_skill = assign_skill_to_job(
            db=db,
            job_id=job_id,
            skill_name=skill_name
        )

        job_skills.append(
            job_skill
        )

    db.flush()

    return job_skills