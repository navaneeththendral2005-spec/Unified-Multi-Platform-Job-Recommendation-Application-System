from sqlalchemy.orm import Session, joinedload

from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.user_skill import UserSkill


# ============================================================
# LEGACY SKILL MATCHING
# ============================================================

def calculate_skill_match(
    user_skills: list[str],
    job_skills: list[str]
) -> float:
    """
    Calculate how well the user's skills match
    the required job skills.

    This function is kept for backward compatibility
    with older parts of the recommendation system.
    """

    if not job_skills:
        return 0.0

    user_skills_lower = {
        skill.strip().lower()
        for skill in user_skills
        if skill and skill.strip()
    }

    job_skills_lower = {
        skill.strip().lower()
        for skill in job_skills
        if skill and skill.strip()
    }

    if not job_skills_lower:
        return 0.0

    matched_skills = (
        user_skills_lower
        .intersection(job_skills_lower)
    )

    match_percentage = (
        len(matched_skills)
        / len(job_skills_lower)
    ) * 100

    return round(
        match_percentage,
        2
    )


# ============================================================
# LEGACY JOB RECOMMENDATIONS
# ============================================================

def recommend_jobs(
    user_skills: list[str],
    jobs: list[dict]
) -> list[dict]:
    """
    Calculate a skill match score for each job
    and return jobs ranked by compatibility.

    This function supports the older dictionary-based
    recommendation workflow.
    """

    recommendations = []

    for job in jobs:

        job_skills = job.get(
            "required_skills",
            []
        )

        match_score = calculate_skill_match(
            user_skills=user_skills,
            job_skills=job_skills
        )

        recommendations.append(
            {
                "job": job,
                "match_score": match_score
            }
        )

    recommendations.sort(
        key=lambda item: item["match_score"],
        reverse=True
    )

    return recommendations


# ============================================================
# GET USER SKILLS FROM SKILL REGISTRY
# ============================================================

def get_user_skill_data(
    db: Session,
    user_id: int
) -> tuple[set[int], dict[int, str]]:
    """
    Get the user's skills from the structured
    Skill Registry.

    Returns:

    - Set of canonical Skill IDs
    - Dictionary mapping Skill IDs to Skill names

    Legacy UserSkill.skill_name values are used
    only as a fallback when no relational skill
    connection exists.
    """

    user_skill_records = (
        db.query(UserSkill)
        .options(
            joinedload(UserSkill.skill)
        )
        .filter(
            UserSkill.user_id == user_id
        )
        .all()
    )

    skill_ids = set()
    skill_names = {}

    for user_skill in user_skill_records:

        # ----------------------------------------------------
        # STRUCTURED SKILL REGISTRY
        # ----------------------------------------------------

        if user_skill.skill_id and user_skill.skill:

            skill_ids.add(
                user_skill.skill_id
            )

            skill_names[
                user_skill.skill_id
            ] = user_skill.skill.name

    return skill_ids, skill_names


# ============================================================
# GET JOB SKILLS FROM SKILL REGISTRY
# ============================================================

def get_job_skill_data(
    db: Session,
    job_id: int
) -> tuple[set[int], dict[int, str]]:
    """
    Get the required skills for a job from the
    structured Skill Registry.

    Returns:

    - Set of canonical Skill IDs
    - Dictionary mapping Skill IDs to Skill names
    """

    job_skill_records = (
        db.query(JobSkill)
        .options(
            joinedload(JobSkill.skill)
        )
        .filter(
            JobSkill.job_id == job_id
        )
        .all()
    )

    skill_ids = set()
    skill_names = {}

    for job_skill in job_skill_records:

        if job_skill.skill_id and job_skill.skill:

            skill_ids.add(
                job_skill.skill_id
            )

            skill_names[
                job_skill.skill_id
            ] = job_skill.skill.name

    return skill_ids, skill_names


# ============================================================
# STRUCTURED SKILL MATCH CALCULATION
# ============================================================

def calculate_structured_skill_match(
    user_skill_ids: set[int],
    job_skill_ids: set[int]
) -> dict:
    """
    Calculate skill compatibility using canonical
    Skill IDs from the central Skill Registry.

    Returns:

    - matched_skill_ids
    - missing_skill_ids
    - total_required_skills
    - matched_skills_count
    - skill_match_percentage
    """

    if not job_skill_ids:

        return {
            "matched_skill_ids": set(),
            "missing_skill_ids": set(),
            "total_required_skills": 0,
            "matched_skills_count": 0,
            "skill_match_percentage": 0.0
        }

    matched_skill_ids = (
        user_skill_ids
        .intersection(job_skill_ids)
    )

    missing_skill_ids = (
        job_skill_ids
        .difference(user_skill_ids)
    )

    skill_match_percentage = (
        len(matched_skill_ids)
        / len(job_skill_ids)
    ) * 100

    return {
        "matched_skill_ids": matched_skill_ids,
        "missing_skill_ids": missing_skill_ids,
        "total_required_skills": len(job_skill_ids),
        "matched_skills_count": len(matched_skill_ids),
        "skill_match_percentage": round(
            skill_match_percentage,
            2
        )
    }


# ============================================================
# DATABASE RECOMMENDATION ENGINE
# ============================================================

def recommend_jobs_from_database(
    db: Session,
    user_id: int
) -> list[dict]:
    """
    Generate job recommendations using the structured
    Skill Registry.

    The recommendation engine compares:

        UserSkill.skill_id
                ↓
             Skill Registry
                ↑
        JobSkill.skill_id

    instead of relying primarily on raw skill strings.
    """

    # --------------------------------------------------------
    # GET USER SKILLS ONCE
    # --------------------------------------------------------

    user_skill_ids, user_skill_names = (
        get_user_skill_data(
            db=db,
            user_id=user_id
        )
    )

    # --------------------------------------------------------
    # GET ALL JOBS
    # --------------------------------------------------------

    jobs = (
        db.query(Job)
        .options(
            joinedload(Job.job_skills)
            .joinedload(JobSkill.skill)
        )
        .all()
    )

    recommendations = []

    # --------------------------------------------------------
    # ANALYZE EVERY JOB
    # --------------------------------------------------------

    for job in jobs:

        job_skill_ids = set()
        job_skill_names = {}

        # ----------------------------------------------------
        # GET STRUCTURED JOB SKILLS
        # ----------------------------------------------------

        for job_skill in job.job_skills:

            if job_skill.skill_id and job_skill.skill:

                job_skill_ids.add(
                    job_skill.skill_id
                )

                job_skill_names[
                    job_skill.skill_id
                ] = job_skill.skill.name

        # ----------------------------------------------------
        # CALCULATE STRUCTURED MATCH
        # ----------------------------------------------------

        match_data = calculate_structured_skill_match(
            user_skill_ids=user_skill_ids,
            job_skill_ids=job_skill_ids
        )

        # ----------------------------------------------------
        # CONVERT MATCHED IDS TO NAMES
        # ----------------------------------------------------

        matched_skills = sorted(
            [
                job_skill_names[skill_id]
                for skill_id in match_data[
                    "matched_skill_ids"
                ]
                if skill_id in job_skill_names
            ],
            key=str.lower
        )

        # ----------------------------------------------------
        # CONVERT MISSING IDS TO NAMES
        # ----------------------------------------------------

        missing_skills = sorted(
            [
                job_skill_names[skill_id]
                for skill_id in match_data[
                    "missing_skill_ids"
                ]
                if skill_id in job_skill_names
            ],
            key=str.lower
        )

        # ----------------------------------------------------
        # BUILD RECOMMENDATION
        # ----------------------------------------------------

        recommendations.append(
            {
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_type": job.job_type,
                "experience_required": (
                    job.experience_required
                ),

                # Structured skills
                "required_skills": sorted(
                    job_skill_names.values(),
                    key=str.lower
                ),

                "matched_skills": matched_skills,

                "missing_skills": missing_skills,

                # Match statistics
                "total_required_skills": (
                    match_data[
                        "total_required_skills"
                    ]
                ),

                "matched_skills_count": (
                    match_data[
                        "matched_skills_count"
                    ]
                ),

                "skill_match_percentage": (
                    match_data[
                        "skill_match_percentage"
                    ]
                ),

                # Backward compatibility
                "match_score": (
                    match_data[
                        "skill_match_percentage"
                    ]
                ),

                "application_link": (
                    job.application_link
                )
            }
        )

    # --------------------------------------------------------
    # RANK JOBS
    # --------------------------------------------------------

    recommendations.sort(
        key=lambda item: (
            item["skill_match_percentage"],
            item["matched_skills_count"]
        ),
        reverse=True
    )

    return recommendations