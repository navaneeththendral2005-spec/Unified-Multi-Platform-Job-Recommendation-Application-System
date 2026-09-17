import re

from app.models.job import Job


# ============================================================
# JOB DOMAIN INTELLIGENCE
# ============================================================

JOB_DOMAIN_RULES = {

    "Artificial Intelligence": [
        "artificial intelligence",
        "ai engineer",
        "ai development",
        "intelligent systems",
        "ai-based",
    ],

    "Machine Learning": [
        "machine learning",
        "machine learning engineer",
        "predictive model",
        "model training",
        "scikit-learn",
        "tensorflow",
        "pytorch",
    ],

    "Deep Learning": [
        "deep learning",
        "neural network",
        "cnn",
        "rnn",
        "transformer",
        "yolo",
    ],

    "Computer Vision": [
        "computer vision",
        "opencv",
        "object detection",
        "image processing",
        "face detection",
        "feature extraction",
    ],

    "Generative AI": [
        "generative ai",
        "large language model",
        "llm",
        "openai",
        "language model",
        "prompt engineering",
    ],

    "Backend Development": [
        "backend",
        "backend developer",
        "fastapi",
        "django",
        "flask",
        "api development",
        "rest api",
        "microservices",
    ],

    "Frontend Development": [
        "frontend",
        "front-end",
        "frontend developer",
        "react",
        "angular",
        "vue",
        "html",
        "css",
        "javascript",
        "typescript",
    ],

    "Full Stack Development": [
        "full stack",
        "full-stack",
        "fullstack",
        "frontend",
        "backend",
    ],

    "Data Science": [
        "data science",
        "data scientist",
        "data analysis",
        "data analytics",
        "pandas",
        "numpy",
        "statistics",
    ],

    "DevOps": [
        "devops",
        "docker",
        "kubernetes",
        "ci/cd",
        "deployment",
        "cloud infrastructure",
    ],

}


# ============================================================
# NORMALIZE SKILLS
# ============================================================

def normalize_skill_list(
    skills: list[str]
) -> list[str]:
    """
    Remove duplicates while preserving order.
    """

    normalized_skills = []

    seen = set()

    for skill in skills:

        if not skill:
            continue

        cleaned_skill = skill.strip()

        if not cleaned_skill:
            continue

        normalized = cleaned_skill.lower()

        if normalized not in seen:

            seen.add(normalized)

            normalized_skills.append(
                cleaned_skill
            )

    return normalized_skills


# ============================================================
# PARSE REQUIRED SKILLS
# ============================================================

def parse_required_skills(
    required_skills: str | None
) -> list[str]:
    """
    Convert stored job skills into a clean list.

    Supports formats such as:

    Python, FastAPI, React

    Python
    FastAPI
    React
    """

    if not required_skills:
        return []

    skills = re.split(

        r"[,;\n|]+",

        required_skills

    )

    return normalize_skill_list(
        skills
    )


# ============================================================
# EXTRACT JOB SKILLS
# ============================================================

def get_job_skills(
    job: Job
) -> list[str]:
    """
    Collect skills from:

    1. Job.required_skills
    2. JobSkill relationship

    Duplicate skills are removed.
    """

    skills = []

    # --------------------------------------------------------
    # REQUIRED SKILLS FIELD
    # --------------------------------------------------------

    skills.extend(

        parse_required_skills(
            job.required_skills
        )

    )

    # --------------------------------------------------------
    # JOB SKILL RELATIONSHIP
    # --------------------------------------------------------

    for job_skill in getattr(
        job,
        "job_skills",
        []
    ):

        skill = getattr(
            job_skill,
            "skill",
            None
        )

        if skill:

            skills.append(
                skill.name
            )

    return normalize_skill_list(
        skills
    )


# ============================================================
# BUILD JOB CONTEXT
# ============================================================

def build_job_context(
    job: Job,
    skills: list[str]
) -> str:
    """
    Combine important job information into
    one searchable intelligence context.
    """

    context_parts = [

        job.title or "",

        job.description or "",

        " ".join(skills),

    ]

    return " ".join(
        context_parts
    ).lower()


# ============================================================
# INFER JOB DOMAINS
# ============================================================

def infer_job_domains(
    job: Job,
    skills: list[str]
) -> list[str]:
    """
    Infer technical domains from:

    - Job title
    - Job description
    - Required skills
    """

    context = build_job_context(
        job=job,
        skills=skills
    )

    detected_domains = []

    for domain, keywords in JOB_DOMAIN_RULES.items():

        for keyword in keywords:

            pattern = (

                r"(?<!\w)"

                + re.escape(keyword.lower())

                + r"(?!\w)"

            )

            if re.search(
                pattern,
                context,
                flags=re.IGNORECASE
            ):

                detected_domains.append(
                    domain
                )

                break

    return detected_domains


# ============================================================
# BUILD JOB INTELLIGENCE PROFILE
# ============================================================

def build_job_profile(
    job: Job
) -> dict:
    """
    Build a structured intelligence profile
    for a job.

    This profile is designed to be consumed
    by the recommendation engine.
    """

    # --------------------------------------------------------
    # EXTRACT JOB SKILLS
    # --------------------------------------------------------

    required_skills = get_job_skills(
        job
    )

    # --------------------------------------------------------
    # INFER DOMAINS
    # --------------------------------------------------------

    domains = infer_job_domains(

        job=job,

        skills=required_skills

    )

    # --------------------------------------------------------
    # RETURN JOB PROFILE
    # --------------------------------------------------------

    return {

        "job_id": job.id,

        "title": job.title,

        "required_skills": required_skills,

        "domains": domains,

        "experience_required": (
            job.experience_required
        ),

        "job_type": job.job_type,

    }