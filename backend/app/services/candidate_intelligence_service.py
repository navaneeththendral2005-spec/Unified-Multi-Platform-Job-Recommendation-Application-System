from sqlalchemy.orm import Session

from app.services.resume_analysis_service import analyze_resume


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(
    items: list[str]
) -> list[str]:
    """
    Remove duplicate values while preserving
    their original order.
    """

    unique_items = []

    seen = set()

    for item in items:

        if not item:
            continue

        normalized_item = (
            item.lower()
            .strip()
        )

        if normalized_item not in seen:

            seen.add(
                normalized_item
            )

            unique_items.append(
                item
            )

    return unique_items


# ============================================================
# EXTRACT PROJECT TECHNOLOGIES
# ============================================================

def get_project_technologies(
    projects: list[dict]
) -> list[str]:
    """
    Collect all technologies detected across
    the candidate's projects.
    """

    technologies = []

    for project in projects:

        project_technologies = project.get(
            "technologies",
            []
        )

        technologies.extend(
            project_technologies
        )

    return remove_duplicates(
        technologies
    )


# ============================================================
# EXTRACT PROJECT DOMAINS
# ============================================================

def get_project_domains(
    projects: list[dict]
) -> list[str]:
    """
    Collect all technical domains inferred
    from the candidate's projects.
    """

    domains = []

    for project in projects:

        project_domains = project.get(
            "domains",
            []
        )

        domains.extend(
            project_domains
        )

    return remove_duplicates(
        domains
    )


# ============================================================
# BUILD CANDIDATE INTELLIGENCE PROFILE
# ============================================================

def build_candidate_profile(
    db: Session,
    resume_text: str | None
) -> dict:
    """
    Build a unified intelligence profile for
    the candidate.

    This profile combines:

    - Resume skills
    - Project technologies
    - Project domains
    - Experience
    - Education
    - Suggested roles
    """

    # --------------------------------------------------------
    # ANALYZE RESUME
    # --------------------------------------------------------

    resume_analysis = analyze_resume(

        db=db,

        text=resume_text

    )

    # --------------------------------------------------------
    # EXTRACT PROJECT DATA
    # --------------------------------------------------------

    projects = resume_analysis.get(
        "projects",
        []
    )

    project_technologies = get_project_technologies(
        projects
    )

    project_domains = get_project_domains(
        projects
    )

    # --------------------------------------------------------
    # BUILD UNIFIED SKILL SET
    # --------------------------------------------------------

    combined_skills = remove_duplicates(

        resume_analysis.get(
            "skills",
            []
        )

        + project_technologies

    )

    # --------------------------------------------------------
    # RETURN CANDIDATE PROFILE
    # --------------------------------------------------------

    return {

        "skills": combined_skills,

        "project_technologies": project_technologies,

        "project_domains": project_domains,

        "experience": resume_analysis.get(
            "experience",
            []
        ),

        "education": resume_analysis.get(
            "education",
            []
        ),

        "suggested_roles": resume_analysis.get(
            "suggested_roles",
            []
        ),

        "projects": projects,

    }