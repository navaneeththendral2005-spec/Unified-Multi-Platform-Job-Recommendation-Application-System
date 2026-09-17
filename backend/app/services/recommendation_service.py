import re

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill
from app.models.user_profile import UserProfile
from app.models.user_skill import UserSkill


# ============================================================
# USER SKILLS
# ============================================================

def get_user_skills(
    db: Session,
    user_id: int
) -> list[str]:
    """
    Get all skill names belonging to a user.

    Uses the relational Skill Registry when available,
    while falling back to the legacy skill_name field.
    """

    user_skills = (
        db.query(UserSkill)
        .filter(UserSkill.user_id == user_id)
        .all()
    )

    skills = []

    for user_skill in user_skills:

        if user_skill.skill:
            skills.append(user_skill.skill.name)

        elif user_skill.skill_name:
            skills.append(user_skill.skill_name)

    return skills


def get_user_skill_ids(
    db: Session,
    user_id: int
) -> set[int]:
    """
    Get all master Skill IDs belonging to a user.
    """

    skill_rows = (
        db.query(UserSkill.skill_id)
        .filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id.isnot(None)
        )
        .all()
    )

    return {
        skill_id
        for (skill_id,) in skill_rows
    }


# ============================================================
# BULK SKILL DATA LOADING
# ============================================================

def get_jobs_skill_map(
    db: Session,
    job_ids: list[int]
) -> dict[int, set[int]]:
    """
    Load skill IDs for all jobs in one database query.

    Returns:

    {
        job_id: {skill_id, skill_id, ...}
    }
    """

    job_skill_map = {
        job_id: set()
        for job_id in job_ids
    }

    if not job_ids:
        return job_skill_map

    rows = (
        db.query(
            JobSkill.job_id,
            JobSkill.skill_id
        )
        .filter(
            JobSkill.job_id.in_(job_ids)
        )
        .all()
    )

    for job_id, skill_id in rows:

        job_skill_map[job_id].add(
            skill_id
        )

    return job_skill_map


def get_skill_name_map(
    db: Session,
    skill_ids: set[int]
) -> dict[int, str]:
    """
    Load skill names for multiple skill IDs
    in one database query.

    Returns:

    {
        skill_id: skill_name
    }
    """

    if not skill_ids:
        return {}

    skills = (
        db.query(Skill)
        .filter(
            Skill.id.in_(skill_ids)
        )
        .all()
    )

    return {
        skill.id: skill.name
        for skill in skills
    }


# ============================================================
# RELATIONAL SKILL MATCHING
# ============================================================

def calculate_skill_match(
    user_skill_ids: set[int],
    job_skill_ids: set[int],
    skill_name_map: dict[int, str]
) -> dict:
    """
    Compare user skills and job skills in memory.

    Matching is performed using Skill IDs.
    """

    matched_skill_ids = (
        user_skill_ids.intersection(
            job_skill_ids
        )
    )

    missing_skill_ids = (
        job_skill_ids.difference(
            user_skill_ids
        )
    )

    matched_skills = sorted(
        [
            skill_name_map.get(
                skill_id,
                "Unknown Skill"
            )
            for skill_id in matched_skill_ids
        ]
    )

    missing_skills = sorted(
        [
            skill_name_map.get(
                skill_id,
                "Unknown Skill"
            )
            for skill_id in missing_skill_ids
        ]
    )

    skill_match_percentage = 0.0

    if job_skill_ids:

        skill_match_percentage = (
            len(matched_skill_ids)
            / len(job_skill_ids)
        ) * 100

    return {
        "matched_skills": matched_skills,

        "missing_skills": missing_skills,

        "skill_match_percentage": round(
            skill_match_percentage,
            2
        )
    }


# ============================================================
# ROLE MATCHING
# ============================================================

def role_matches(
    role: str,
    job_title: str
) -> bool:
    """
    Check whether a role matches a job title.
    """

    if not role or not job_title:
        return False

    role = role.lower().strip()

    job_title = job_title.lower().strip()

    return (
        role in job_title
        or job_title in role
    )


def has_preferred_role_match(
    profile: UserProfile,
    job: Job
) -> bool:
    """
    Check whether the job matches the user's
    preferred job role.
    """

    if not profile.preferred_job_role:
        return False

    return role_matches(
        profile.preferred_job_role,
        job.title
    )


# ============================================================
# LOCATION MATCHING
# ============================================================

def has_location_match(
    profile: UserProfile,
    job: Job
) -> bool:
    """
    Check whether the job matches the user's
    preferred location.
    """

    if not profile.preferred_location:
        return False

    if not job.location:
        return False

    preferred_location = (
        profile.preferred_location
        .lower()
        .strip()
    )

    job_location = (
        job.location
        .lower()
        .strip()
    )

    return (
        preferred_location in job_location
        or job_location in preferred_location
    )


# ============================================================
# EXPERIENCE MATCHING
# ============================================================

def extract_experience_years(
    experience_required: str | None
) -> int | None:
    """
    Extract experience years from job requirements.
    """

    if not experience_required:
        return None

    experience_text = (
        experience_required
        .lower()
        .strip()
    )

    if "fresher" in experience_text:
        return 0

    match = re.search(
        r"\d+",
        experience_text
    )

    if match:
        return int(
            match.group()
        )

    return None


def calculate_experience_match(
    user_experience: int | None,
    job_experience_required: str | None
) -> float:
    """
    Calculate experience match points out of 10.
    """

    required_years = (
        extract_experience_years(
            job_experience_required
        )
    )

    if user_experience is None:
        return 0.0

    if required_years is None:
        return 0.0

    if user_experience >= required_years:
        return 10.0

    difference = (
        required_years
        - user_experience
    )

    if difference == 1:
        return 7.0

    if difference == 2:
        return 4.0

    return 0.0


def get_experience_reason(
    profile: UserProfile,
    job: Job
) -> str | None:
    """
    Generate a human-readable experience reason.
    """

    if profile.experience_years is None:
        return None

    if not job.experience_required:
        return None

    required_years = (
        extract_experience_years(
            job.experience_required
        )
    )

    if required_years is None:
        return None

    user_years = profile.experience_years

    if user_years >= required_years:

        return (
            f"Your {user_years} years of experience "
            f"meet the job requirement of "
            f"{required_years} years"
        )

    if required_years - user_years == 1:

        return (
            f"You are close to the required experience "
            f"level of {required_years} years"
        )

    return (
        f"This role requires {required_years} years "
        f"of experience, while your profile shows "
        f"{user_years} years"
    )


# ============================================================
# MATCH LEVEL
# ============================================================

def get_match_level(
    score: float
) -> str:
    """
    Convert recommendation score into
    a human-readable match level.
    """

    if score >= 75:
        return "Excellent Match"

    if score >= 50:
        return "Good Match"

    if score >= 25:
        return "Moderate Match"

    return "Low Match"


# ============================================================
# RECOMMENDATION SCORE
# ============================================================

def calculate_recommendation_score(
    profile: UserProfile,
    job: Job,
    user_skill_ids: set[int],
    job_skill_ids: set[int],
    skill_name_map: dict[int, str]
) -> tuple[float, dict]:
    """
    Calculate the recommendation score for a job.
    """

    score = 0.0

    # --------------------------------------------------------
    # SKILL MATCH
    # --------------------------------------------------------

    skill_match_data = calculate_skill_match(
        user_skill_ids=user_skill_ids,
        job_skill_ids=job_skill_ids,
        skill_name_map=skill_name_map
    )

    skill_match_percentage = (
        skill_match_data[
            "skill_match_percentage"
        ]
    )

    score += (
        skill_match_percentage / 100
    ) * 50

    # --------------------------------------------------------
    # PREFERRED ROLE MATCH
    # --------------------------------------------------------

    if has_preferred_role_match(
        profile,
        job
    ):

        score += 25

    # --------------------------------------------------------
    # PREFERRED LOCATION MATCH
    # --------------------------------------------------------

    if has_location_match(
        profile,
        job
    ):

        score += 15

    # --------------------------------------------------------
    # EXPERIENCE MATCH
    # --------------------------------------------------------

    experience_score = (
        calculate_experience_match(
            profile.experience_years,
            job.experience_required
        )
    )

    score += experience_score

    return (
        round(score, 2),
        skill_match_data
    )


# ============================================================
# RECOMMENDATION REASONS
# ============================================================

def generate_recommendation_reasons(
    profile: UserProfile,
    job: Job,
    skill_match_data: dict
) -> list[str]:
    """
    Generate human-readable explanations for why
    a job was recommended.
    """

    reasons = []

    matched_skills = (
        skill_match_data[
            "matched_skills"
        ]
    )

    if matched_skills:

        reasons.append(
            f"Matched skills: "
            f"{', '.join(matched_skills)}"
        )

    missing_skills = (
        skill_match_data[
            "missing_skills"
        ]
    )

    if missing_skills:

        reasons.append(
            f"Skills to improve: "
            f"{', '.join(missing_skills)}"
        )

    if has_preferred_role_match(
        profile,
        job
    ):

        reasons.append(
            "Matches your preferred job role"
        )

    if has_location_match(
        profile,
        job
    ):

        reasons.append(
            "Matches your preferred location"
        )

    experience_reason = (
        get_experience_reason(
            profile,
            job
        )
    )

    if experience_reason:

        reasons.append(
            experience_reason
        )

    if not reasons:

        reasons.append(
            "Recommended based on overall profile compatibility"
        )

    return reasons


# ============================================================
# MAIN RECOMMENDATION ENGINE
# ============================================================

def get_recommendations(
    db: Session,
    user_id: int,
    profile: UserProfile,
    jobs: list[Job]
) -> list[dict]:
    """
    Generate, score, explain, rank,
    and return job recommendations.

    Skill data is loaded efficiently in bulk
    before recommendation scoring begins.
    """

    # --------------------------------------------------------
    # LOAD USER SKILLS ONCE
    # --------------------------------------------------------

    user_skill_ids = get_user_skill_ids(
        db,
        user_id
    )

    # --------------------------------------------------------
    # GET ALL JOB IDS
    # --------------------------------------------------------

    job_ids = [
        job.id
        for job in jobs
    ]

    # --------------------------------------------------------
    # LOAD ALL JOB SKILLS ONCE
    # --------------------------------------------------------

    job_skill_map = get_jobs_skill_map(
        db,
        job_ids
    )

    # --------------------------------------------------------
    # COLLECT ALL SKILL IDS
    # --------------------------------------------------------

    all_skill_ids = set(
        user_skill_ids
    )

    for job_skill_ids in job_skill_map.values():

        all_skill_ids.update(
            job_skill_ids
        )

    # --------------------------------------------------------
    # LOAD SKILL NAMES ONCE
    # --------------------------------------------------------

    skill_name_map = get_skill_name_map(
        db,
        all_skill_ids
    )

    recommendations = []

    # --------------------------------------------------------
    # SCORE JOBS IN MEMORY
    # --------------------------------------------------------

    for job in jobs:

        job_skill_ids = (
            job_skill_map.get(
                job.id,
                set()
            )
        )

        (
            match_score,
            skill_match_data
        ) = calculate_recommendation_score(
            profile=profile,
            job=job,
            user_skill_ids=user_skill_ids,
            job_skill_ids=job_skill_ids,
            skill_name_map=skill_name_map
        )

        # ----------------------------------------------------
        # FILTER VERY WEAK RECOMMENDATIONS
        # ----------------------------------------------------

        if match_score < 20:
            continue

        # ----------------------------------------------------
        # GENERATE EXPLANATIONS
        # ----------------------------------------------------

        reasons = generate_recommendation_reasons(
            profile,
            job,
            skill_match_data
        )

        # ----------------------------------------------------
        # ADD RESULT
        # ----------------------------------------------------

        required_skills = sorted(
            [
                skill_name_map.get(
                    skill_id,
                    "Unknown Skill"
                )
                for skill_id in job_skill_ids
            ]
        )       

        recommendations.append({

            "job": job,

            "required_skills": required_skills,

            "match_score": match_score,

            "match_level": get_match_level(
                match_score
            ),

            "skill_match_percentage": (
                skill_match_data[
                    "skill_match_percentage"
                ]
            ),

            "matched_skills": (
                skill_match_data[
                    "matched_skills"
                ]
            ),

            "missing_skills": (
                skill_match_data[
                    "missing_skills"
                ]
            ),

            "reasons": reasons
        })

    # --------------------------------------------------------
    # SORT BEST MATCHES FIRST
    # --------------------------------------------------------

    recommendations.sort(
        key=lambda item: item["match_score"],
        reverse=True
    )

    # --------------------------------------------------------
    # RETURN TOP 5
    # --------------------------------------------------------

    return recommendations[:5]


# ============================================================
# DATABASE RECOMMENDATION ENTRY POINT
# ============================================================

def generate_user_recommendations(
    db: Session,
    user_id: int
) -> list[dict] | None:
    """
    Main database entry point for generating
    recommendations for a user.
    """

    profile = (
        db.query(UserProfile)
        .filter(
            UserProfile.user_id == user_id
        )
        .first()
    )

    if not profile:
        return None

    jobs = (
        db.query(Job)
        .order_by(Job.id)
        .all()
    )

    return get_recommendations(
        db=db,
        user_id=user_id,
        profile=profile,
        jobs=jobs
    )