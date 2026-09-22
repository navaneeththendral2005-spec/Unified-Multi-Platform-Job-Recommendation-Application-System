from datetime import datetime

from app.integrations.job_sources.normalized import NormalizedJob
from app.models.job import Job
from app.models.job_source_listing import JobSourceListing
from app.services.job_ingestion_service import JobIngestionService
from app.utils.time import utc_now


def test_job_ingestion_creates_canonical_job_and_listing(db_session):
    service = JobIngestionService(db_session)

    job = NormalizedJob(
        source_name="test_source",
        external_job_id="TEST-001",
        title="Python Backend Developer",
        company_name="Test Technologies",
        description="Build backend services using Python.",
        location="Chennai",
        job_type="Full-time",
        experience_required="1-3 years",
        application_url="https://example.com/jobs/TEST-001",
        posted_at=utc_now(),
        skills=["Python", "FastAPI", "PostgreSQL"],
        raw_payload={
            "id": "TEST-001",
            "source": "test_source",
        },
    )

    canonical_job = service.ingest(job)

    assert canonical_job.id is not None
    assert canonical_job.title == "Python Backend Developer"
    assert canonical_job.company == "Test Technologies"
    assert canonical_job.company_id is not None

    listing = (
        db_session.query(JobSourceListing)
        .filter(
            JobSourceListing.external_job_id == "TEST-001"
        )
        .one()
    )

    assert listing.job_id == canonical_job.id
    assert listing.original_url == (
        "https://example.com/jobs/TEST-001"
    )
    assert listing.is_active is True


def test_duplicate_source_listing_does_not_create_duplicate_job(
    db_session,
):
    service = JobIngestionService(db_session)

    job = NormalizedJob(
        source_name="test_source",
        external_job_id="TEST-002",
        title="Python Developer",
        company_name="Test Technologies",
        description="Python backend development.",
        location="Chennai",
        application_url="https://example.com/jobs/TEST-002",
        skills=["Python"],
        raw_payload={"id": "TEST-002"},
    )

    first_job = service.ingest(job)
    second_job = service.ingest(job)

    assert first_job.id == second_job.id

    jobs = (
        db_session.query(Job)
        .filter(
            Job.title == "Python Developer",
            Job.company == "Test Technologies",
        )
        .all()
    )

    assert len(jobs) == 1

    listings = (
        db_session.query(JobSourceListing)
        .filter(
            JobSourceListing.external_job_id == "TEST-002"
        )
        .all()
    )

    assert len(listings) == 1