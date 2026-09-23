import os
import re

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill
from app.models.user_preference import UserPreference
from app.models.user_profile import UserProfile
from app.models.user_skill import UserSkill
from app.services.advanced_matching import (
    parse_skill_string,
    score_candidate_job,
)


# ============================================================
# USER SKILLS
# ============================================================

def get_user_skills(
    db: Session,
    user_id: int,
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
    user_id: int,
) -> set[int]:
    """Get all master Skill IDs belonging to a user."""
    skill_rows = (
        db.query(UserSkill.skill_id)
        .filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_id.isnot(None),
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
    job_ids: list[int],
) -> dict[int, set[int]]:
    """Load skill IDs for all jobs in one database query."""
    job_skill_map = {
        job_id: set()
        for job_id in job_ids
    }

    if not job_ids:
        return job_skill_map

    rows = (
        db.query(
            JobSkill.job_id,
            JobSkill.skill_id,
        )
        .filter(JobSkill.job_id.in_(job_ids))
        .all()
    )

    for job_id, skill_id in rows:
        job_skill_map[job_id].add(skill_id)

    return job_skill_map


def get_skill_name_map(
    db: Session,
    skill_ids: set[int],
) -> dict[int, str]:
    """Load skill names for multiple skill IDs in one query."""
    if not skill_ids:
        return {}

    skills = (
        db.query(Skill)
        .filter(Skill.id.in_(skill_ids))
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
    skill_name_map: dict[int, str],
) -> dict:
    """Compare user skills and job skills in memory."""
    matched_skill_ids = user_skill_ids.intersection(job_skill_ids)
    missing_skill_ids = job_skill_ids.difference(user_skill_ids)

    matched_skills = sorted(
        [
            skill_name_map.get(skill_id, "Unknown Skill")
            for skill_id in matched_skill_ids
        ]
    )

    missing_skills = sorted(
        [
            skill_name_map.get(skill_id, "Unknown Skill")
            for skill_id in missing_skill_ids
        ]
    )

    skill_match_percentage = 0.0

    if job_skill_ids:
        skill_match_percentage = (
            len(matched_skill_ids) / len(job_skill_ids)
        ) * 100

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "skill_match_percentage": round(skill_match_percentage, 2),
    }


# ============================================================
# LEGACY MATCHING HELPERS
# ============================================================

def role_matches(role: str, job_title: str) -> bool:
    """Check whether a role matches a job title."""
    if not role or not job_title:
        return False

    role = role.lower().strip()
    job_title = job_title.lower().strip()

    return role in job_title or job_title in role


def has_preferred_role_match(
    profile: UserProfile,
    job: Job,
) -> bool:
    """Check whether the job matches the user's preferred role."""
    if not profile.preferred_job_role:
        return False

    return role_matches(
        profile.preferred_job_role,
        job.title,
    )


def has_location_match(
    profile: UserProfile,
    job: Job,
) -> bool:
    """Check whether the job matches the user's preferred location."""
    if not profile.preferred_location or not job.location:
        return False

    preferred_location = profile.preferred_location.lower().strip()
    job_location = job.location.lower().strip()

    return (
        preferred_location in job_location
        or job_location in preferred_location
    )


def extract_experience_years(
    experience_required: str | None,
) -> int | None:
    """Extract experience years from job requirements."""
    if not experience_required:
        return None

    experience_text = experience_required.lower().strip()

    if "fresher" in experience_text:
        return 0

    match = re.search(r"\d+", experience_text)

    if match:
        return int(match.group())

    return None


def calculate_experience_match(
    user_experience: int | None,
    job_experience_required: str | None,
) -> float:
    """Calculate experience match points out of 10."""
    required_years = extract_experience_years(job_experience_required)

    if user_experience is None or required_years is None:
        return 0.0

    if user_experience >= required_years:
        return 10.0

    difference = required_years - user_experience

    if difference == 1:
        return 7.0

    if difference == 2:
        return 4.0

    return 0.0


def get_experience_reason(
    profile: UserProfile,
    job: Job,
) -> str | None:
    """Generate a human-readable experience reason."""
    if profile.experience_years is None:
        return None

    if not job.experience_required:
        return None

    required_years = extract_experience_years(job.experience_required)

    if required_years is None:
        return None

    user_years = profile.experience_years

    if user_years >= required_years:
        return (
            f"Your {user_years} years of experience meet the job "
            f"requirement of {required_years} years"
        )

    if required_years - user_years == 1:
        return (
            f"You are close to the required experience level of "
            f"{required_years} years"
        )

    return (
        f"This role requires {required_years} years of experience, "
        f"while your profile shows {user_years} years"
    )


def get_match_level(score: float) -> str:
    """Convert recommendation score into a human-readable match level."""
    if score >= 75:
        return "Excellent Match"

    if score >= 50:
        return "Good Match"

    if score >= 25:
        return "Moderate Match"

    return "Low Match"


# ============================================================
# LEGACY RECOMMENDATION SCORE
# ============================================================

def calculate_recommendation_score(
    profile: UserProfile,
    job: Job,
    user_skill_ids: set[int],
    job_skill_ids: set[int],
    skill_name_map: dict[int, str],
) -> tuple[float, dict]:
    """Calculate the original recommendation score."""
    score = 0.0

    skill_match_data = calculate_skill_match(
        user_skill_ids=user_skill_ids,
        job_skill_ids=job_skill_ids,
        skill_name_map=skill_name_map,
    )

    skill_match_percentage = skill_match_data["skill_match_percentage"]
    score += (skill_match_percentage / 100) * 50

    if has_preferred_role_match(profile, job):
        score += 25

    if has_location_match(profile, job):
        score += 15

    experience_score = calculate_experience_match(
        profile.experience_years,
        job.experience_required,
    )
    score += experience_score

    return round(score, 2), skill_match_data


# ============================================================
# RECOMMENDATION REASONS
# ============================================================

def generate_recommendation_reasons(
    profile: UserProfile,
    job: Job,
    skill_match_data: dict,
) -> list[str]:
    """Generate human-readable explanations for a recommendation."""
    reasons = []

    matched_skills = skill_match_data["matched_skills"]

    if matched_skills:
        reasons.append(
            f"Matched skills: {', '.join(matched_skills)}"
        )

    missing_skills = skill_match_data["missing_skills"]

    if missing_skills:
        reasons.append(
            f"Skills to improve: {', '.join(missing_skills)}"
        )

    if has_preferred_role_match(profile, job):
        reasons.append("Matches your preferred job role")

    if has_location_match(profile, job):
        reasons.append("Matches your preferred location")

    experience_reason = get_experience_reason(profile, job)

    if experience_reason:
        reasons.append(experience_reason)

    if not reasons:
        reasons.append(
            "Recommended based on overall profile compatibility"
        )

    return reasons


# ============================================================
# ADVANCED RECOMMENDATION HELPERS
# ============================================================

def _csv_values(value: str | None) -> list[str]:
    """Normalize comma-separated preference values."""
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def _preference_values(
    preferences: UserPreference | None,
    profile: UserProfile,
    field_name: str,
) -> list[str]:
    """
    Read a preference field when available.

    The profile remains the fallback so the existing recommendation
    behavior is preserved for users without the newer preference data.
    """
    value = (
        getattr(preferences, field_name, None)
        if preferences is not None
        else None
    )

    values = _csv_values(value)

    if values:
        return values

    profile_value = getattr(
        profile,
        field_name,
        None,
    )

    if profile_value:
        return [str(profile_value).strip()]

    return []


def _advanced_recommendation(
    profile: UserProfile,
    job: Job,
    candidate_skills: list[str],
    preferred_roles: list[str],
    preferred_locations: list[str],
) -> tuple[float, dict, list[str]]:
    """
    Run the new weighted, explainable matcher.

    The advanced matcher is intentionally isolated from the legacy
    relational matcher so the existing engine remains available as a
    compatibility fallback.
    """
    job_skill_text = getattr(job, "required_skills", None)

    if not job_skill_text:
        job_skill_text = getattr(job, "skills", None)

    if job_skill_text:
        parsed_job_skills = parse_skill_string(job_skill_text)
    else:
        parsed_job_skills = []

    candidate_experience = profile.experience_years

    result = score_candidate_job(
        candidate_skills=candidate_skills,
        required_skills=parsed_job_skills,
        preferred_roles=preferred_roles,
        preferred_locations=preferred_locations,
        job_title=getattr(job, "title", "") or "",
        job_location=getattr(job, "location", "") or "",
        candidate_experience_years=candidate_experience,
        required_experience=getattr(job, "experience_required", None),
        candidate_domains=None,
        job_domains=None,
    )

    score = float(result.score)

    breakdown = {
        "skills": round(float(result.skill_score), 2),
        "role": round(float(result.role_score), 2),
        "location": round(float(result.location_score), 2),
        "experience": round(float(result.experience_score), 2),
        "domain": round(float(result.domain_score), 2),
    }

    reasons = list(result.reasons)

    return score, breakdown, reasons


# ============================================================
# MAIN RECOMMENDATION ENGINE
# ============================================================

def get_recommendations(
    db: Session,
    user_id: int,
    profile: UserProfile,
    jobs: list[Job],
    preferences: UserPreference | None = None,
) -> list[dict]:
    """
    Generate, score, explain, rank, and return recommendations.

    The advanced engine is the default. Set
    RECOMMENDATION_ENGINE_MODE=legacy to retain the original scoring
    behavior.
    """
    user_skill_ids = get_user_skill_ids(db, user_id)
    candidate_skills = get_user_skills(db, user_id)

    job_ids = [job.id for job in jobs]
    job_skill_map = get_jobs_skill_map(db, job_ids)

    all_skill_ids = set(user_skill_ids)

    for job_skill_ids in job_skill_map.values():
        all_skill_ids.update(job_skill_ids)

    skill_name_map = get_skill_name_map(db, all_skill_ids)

    preferred_roles = _preference_values(
        preferences,
        profile,
        "preferred_roles",
    )

    if not preferred_roles and profile.preferred_job_role:
        preferred_roles = [profile.preferred_job_role]

    preferred_locations = _preference_values(
        preferences,
        profile,
        "preferred_locations",
    )

    if not preferred_locations and profile.preferred_location:
        preferred_locations = [profile.preferred_location]

    engine_mode = os.getenv(
        "RECOMMENDATION_ENGINE_MODE",
        "advanced",
    ).strip().lower()

    recommendations = []

    for job in jobs:
        job_skill_ids = job_skill_map.get(job.id, set())

        relational_skill_match = calculate_skill_match(
            user_skill_ids=user_skill_ids,
            job_skill_ids=job_skill_ids,
            skill_name_map=skill_name_map,
        )

        if engine_mode == "legacy":
            match_score, score_data = calculate_recommendation_score(
                profile=profile,
                job=job,
                user_skill_ids=user_skill_ids,
                job_skill_ids=job_skill_ids,
                skill_name_map=skill_name_map,
            )

            score_breakdown = {
                "skills": round(
                    score_data["skill_match_percentage"] * 0.50,
                    2,
                ),
                "role": (
                    25.0
                    if has_preferred_role_match(profile, job)
                    else 0.0
                ),
                "location": (
                    15.0
                    if has_location_match(profile, job)
                    else 0.0
                ),
                "experience": round(
                    calculate_experience_match(
                        profile.experience_years,
                        job.experience_required,
                    ),
                    2,
                ),
                "domain": 0.0,
            }

            reasons = generate_recommendation_reasons(
                profile,
                job,
                score_data,
            )
        else:
            try:
                match_score, score_breakdown, reasons = (
                    _advanced_recommendation(
                        profile=profile,
                        job=job,
                        candidate_skills=candidate_skills,
                        preferred_roles=preferred_roles,
                        preferred_locations=preferred_locations,
                    )
                )
            except (AttributeError, TypeError, ValueError):
                # Keep recommendation generation resilient when an
                # individual legacy job record lacks fields required
                # by the advanced matcher.
                match_score, score_data = calculate_recommendation_score(
                    profile=profile,
                    job=job,
                    user_skill_ids=user_skill_ids,
                    job_skill_ids=job_skill_ids,
                    skill_name_map=skill_name_map,
                )

                score_breakdown = {
                    "skills": round(
                        score_data["skill_match_percentage"] * 0.50,
                        2,
                    ),
                    "role": (
                        25.0
                        if has_preferred_role_match(profile, job)
                        else 0.0
                    ),
                    "location": (
                        15.0
                        if has_location_match(profile, job)
                        else 0.0
                    ),
                    "experience": round(
                        calculate_experience_match(
                            profile.experience_years,
                            job.experience_required,
                        ),
                        2,
                    ),
                    "domain": 0.0,
                }

                reasons = generate_recommendation_reasons(
                    profile,
                    job,
                    score_data,
                )

        if match_score < 20:
            continue

        required_skills = sorted(
            [
                skill_name_map.get(
                    skill_id,
                    "Unknown Skill",
                )
                for skill_id in job_skill_ids
            ]
        )

        recommendations.append(
            {
                "job": job,
                "required_skills": required_skills,
                "match_score": round(float(match_score), 2),
                "match_level": get_match_level(float(match_score)),
                "skill_match_percentage": (
                    relational_skill_match["skill_match_percentage"]
                ),
                "matched_skills": relational_skill_match["matched_skills"],
                "missing_skills": relational_skill_match["missing_skills"],
                "reasons": reasons,
                "score_breakdown": score_breakdown,
            }
        )

    recommendations.sort(
        key=lambda item: item["match_score"],
        reverse=True,
    )

    return recommendations[:5]


# ============================================================
# DATABASE RECOMMENDATION ENTRY POINT
# ============================================================

def generate_user_recommendations(
    db: Session,
    user_id: int,
) -> list[dict] | None:
    """Main database entry point for generating recommendations."""
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == user_id)
        .first()
    )

    if not profile:
        return None

    preferences = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == user_id)
        .first()
    )

    jobs = (
        db.query(Job)
        .order_by(Job.id)
        .all()
    )

    return get_recommendations(
        db=db,
        user_id=user_id,
        profile=profile,
        jobs=jobs,
        preferences=preferences,
    )
