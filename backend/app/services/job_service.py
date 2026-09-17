from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill

from app.schemas.job import JobCreate

from app.services.skill_extraction_service import (
    extract_skills_from_text
)


# ============================================================
# BUILD JOB TEXT FOR SKILL INTELLIGENCE
# ============================================================

def build_job_skill_text(
    job: JobCreate
) -> str:
    """
    Combine all relevant job fields into a single
    text source for centralized skill extraction.
    """

    job_content = [

        job.title,

        job.description,

        job.required_skills or ""

    ]

    return " ".join(
        content
        for content in job_content
        if content
    )


# ============================================================
# CREATE JOB SKILL MAPPINGS
# ============================================================

def create_job_skill_mappings(
    db: Session,
    job: Job,
    detected_skill_names: list[str]
) -> None:
    """
    Create JobSkill mappings using canonical skills
    detected by the central Skill Registry.

    The detected skill names are already normalized
    to canonical Skill names by:

    extract_skills_from_text()
    """

    if not detected_skill_names:
        return

    # --------------------------------------------------------
    # LOAD CANONICAL SKILL RECORDS
    # --------------------------------------------------------

    skills = (

        db.query(Skill)

        .filter(
            Skill.name.in_(
                detected_skill_names
            )
        )

        .all()

    )

    # --------------------------------------------------------
    # CREATE JOB ↔ SKILL RELATIONSHIPS
    # --------------------------------------------------------

    for skill in skills:

        job_skill = JobSkill(

            job_id=job.id,

            skill_id=skill.id

        )

        db.add(
            job_skill
        )


# ============================================================
# CREATE INTELLIGENT JOB
# ============================================================

def create_job(
    db: Session,
    job: JobCreate
):
    """
    Create a job and automatically generate its
    structured JobSkill intelligence.

    Pipeline:

    Job Creation
        ↓
    Combine Job Content
        ↓
    Extract Canonical Skills
        ↓
    Resolve Skill Records
        ↓
    Create JobSkill Mappings
        ↓
    Commit Intelligent Job
    """

    # --------------------------------------------------------
    # CREATE JOB RECORD
    # --------------------------------------------------------

    new_job = Job(

        title=job.title,

        company=job.company,

        description=job.description,

        required_skills=job.required_skills,

        location=job.location,

        job_type=job.job_type,

        experience_required=job.experience_required,

        application_link=job.application_link

    )

    db.add(
        new_job
    )

    # Flush generates the Job ID without committing yet.

    db.flush()


    # --------------------------------------------------------
    # BUILD JOB CONTENT
    # --------------------------------------------------------

    job_text = build_job_skill_text(
        job
    )


    # --------------------------------------------------------
    # EXTRACT CANONICAL SKILLS
    # --------------------------------------------------------

    detected_skill_names = extract_skills_from_text(

        db=db,

        text=job_text

    )


    # --------------------------------------------------------
    # CREATE JOB SKILL MAPPINGS
    # --------------------------------------------------------

    create_job_skill_mappings(

        db=db,

        job=new_job,

        detected_skill_names=detected_skill_names

    )


    # --------------------------------------------------------
    # COMMIT EVERYTHING TOGETHER
    # --------------------------------------------------------

    db.commit()

    db.refresh(
        new_job
    )


    return new_job


# ============================================================
# GET ALL JOBS
# ============================================================

def get_all_jobs(
    db: Session
):

    return (

        db.query(Job)

        .all()

    )


# ============================================================
# GET JOB BY ID
# ============================================================

def get_job_by_id(

    db: Session,

    job_id: int

):

    return (

        db.query(Job)

        .filter(

            Job.id == job_id

        )

        .first()

    )