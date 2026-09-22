from datetime import datetime
import json
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.integrations.job_sources.normalized import NormalizedJob
from app.models.company import Company
from app.models.job import Job
from app.models.job_source import JobSource
from app.models.job_source_listing import JobSourceListing
from app.utils.time import utc_now


class JobIngestionService:
    """
    Converts normalized jobs from external platforms into the
    canonical Job + JobSourceListing database structure.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def ingest(self, normalized_job: NormalizedJob) -> Job:
        """
        Ingest one normalized external job.

        The process is:

        1. Resolve the source platform.
        2. Resolve or create the company.
        3. Check whether this exact source listing already exists.
        4. Find an existing canonical job when possible.
        5. Otherwise create a new canonical job.
        6. Create or update the source listing.
        """

        source = self._get_or_create_source(
            normalized_job.source_name
        )

        company = self._get_or_create_company(
            normalized_job.company_name
        )

        existing_listing = self._find_existing_listing(
            source_id=source.id,
            external_job_id=normalized_job.external_job_id,
        )

        if existing_listing:
            job = existing_listing.job

            self._update_listing(
                existing_listing,
                normalized_job,
            )

            self._update_canonical_job(
                job,
                normalized_job,
                company,
            )

            self.db.commit()
            self.db.refresh(job)

            return job

        job = self._find_canonical_job(
            normalized_job,
            company,
        )

        if job is None:
            job = self._create_canonical_job(
                normalized_job,
                company,
            )

            self.db.add(job)
            self.db.flush()

        listing = self._create_source_listing(
            normalized_job,
            source,
            job,
        )

        self.db.add(listing)

        self.db.commit()
        self.db.refresh(job)

        return job

    # ------------------------------------------------------------------
    # Bulk ingestion
    # ------------------------------------------------------------------

    def ingest_many(
        self,
        normalized_jobs: list[NormalizedJob],
    ) -> list[Job]:
        """
        Ingest multiple normalized jobs through the canonical
        ingestion pipeline.
        """

        return [
            self.ingest(normalized_job)
            for normalized_job in normalized_jobs
        ]

    # ------------------------------------------------------------------
    # Source
    # ------------------------------------------------------------------

    def _get_or_create_source(
        self,
        source_name: str,
    ) -> JobSource:
        normalized_name = self._normalize_text(source_name)

        source = self.db.scalar(
            select(JobSource).where(
                func.lower(JobSource.name) == normalized_name
            )
        )

        if source:
            return source

        source = JobSource(
            name=normalized_name,
            display_name=source_name.strip(),
            source_type="EXTERNAL",
            is_active=True,
            health_status="UNKNOWN",
        )

        self.db.add(source)
        self.db.flush()

        return source

    # ------------------------------------------------------------------
    # Company
    # ------------------------------------------------------------------

    def _get_or_create_company(
        self,
        company_name: str,
    ) -> Company:
        normalized_name = self._normalize_company_name(
            company_name
        )

        company = self.db.scalar(
            select(Company).where(
                Company.normalized_name == normalized_name
            )
        )

        if company:
            return company

        company = Company(
            name=company_name.strip(),
            normalized_name=normalized_name,
        )

        self.db.add(company)
        self.db.flush()

        return company

    # ------------------------------------------------------------------
    # Existing source listing
    # ------------------------------------------------------------------

    def _find_existing_listing(
        self,
        *,
        source_id: int,
        external_job_id: str,
    ) -> JobSourceListing | None:
        return self.db.scalar(
            select(JobSourceListing)
            .where(
                JobSourceListing.source_id == source_id,
                JobSourceListing.external_job_id
                == external_job_id,
            )
        )

    # ------------------------------------------------------------------
    # Canonical job detection
    # ------------------------------------------------------------------

    def _find_canonical_job(
        self,
        normalized_job: NormalizedJob,
        company: Company,
    ) -> Job | None:
        """
        Conservative canonical-job matching.

        Currently matches using:

        - company
        - normalized title
        - normalized location

        This intentionally avoids aggressive fuzzy matching.
        A more advanced fingerprint/deduplication engine can be
        added later without changing the source adapters.
        """

        normalized_title = self._normalize_text(
            normalized_job.title
        )

        normalized_location = self._normalize_text(
            normalized_job.location or ""
        )

        statement = select(Job).where(
            Job.company_id == company.id,
            func.lower(func.trim(Job.title))
            == normalized_title,
        )

        if normalized_location:
            statement = statement.where(
                func.lower(
                    func.trim(
                        func.coalesce(Job.location, "")
                    )
                )
                == normalized_location
            )

        return self.db.scalar(statement.limit(1))

    # ------------------------------------------------------------------
    # Canonical Job creation
    # ------------------------------------------------------------------

    def _create_canonical_job(
        self,
        normalized_job: NormalizedJob,
        company: Company,
    ) -> Job:
        required_skills = ", ".join(
            skill.strip()
            for skill in normalized_job.skills
            if skill and skill.strip()
        )

        return Job(
            title=normalized_job.title.strip(),
            company=company.name,
            company_id=company.id,
            description=normalized_job.description or "",
            required_skills=required_skills or None,
            location=normalized_job.location,
            job_type=normalized_job.job_type,
            experience_required=normalized_job.experience_required,
            application_link=normalized_job.application_url,
            posted_at=normalized_job.posted_at,
        )

    # ------------------------------------------------------------------
    # Canonical Job update
    # ------------------------------------------------------------------

    def _update_canonical_job(
        self,
        job: Job,
        normalized_job: NormalizedJob,
        company: Company,
    ) -> None:
        """
        Update canonical fields conservatively.

        Source-specific information remains on JobSourceListing.
        """

        job.company_id = company.id
        job.company = company.name

        if not job.description and normalized_job.description:
            job.description = normalized_job.description

        if not job.location and normalized_job.location:
            job.location = normalized_job.location

        if not job.job_type and normalized_job.job_type:
            job.job_type = normalized_job.job_type

        if (
            not job.experience_required
            and normalized_job.experience_required
        ):
            job.experience_required = (
                normalized_job.experience_required
            )

        if (
            not job.application_link
            and normalized_job.application_url
        ):
            job.application_link = normalized_job.application_url

        if not job.posted_at and normalized_job.posted_at:
            job.posted_at = normalized_job.posted_at

        if not job.required_skills and normalized_job.skills:
            job.required_skills = ", ".join(
                skill.strip()
                for skill in normalized_job.skills
                if skill and skill.strip()
            )

    # ------------------------------------------------------------------
    # Source listing creation
    # ------------------------------------------------------------------

    def _create_source_listing(
        self,
        normalized_job: NormalizedJob,
        source: JobSource,
        job: Job,
    ) -> JobSourceListing:
        """
        Create a source-specific listing.

        first_seen_at and last_seen_at represent when our system
        observed the listing, not when the external platform
        originally published the job.
        """

        now = utc_now()

        return JobSourceListing(
            job_id=job.id,
            source_id=source.id,
            external_job_id=normalized_job.external_job_id,
            original_url=normalized_job.application_url,
            source_title=normalized_job.title,
            source_company_name=normalized_job.company_name,
            raw_description=normalized_job.description,
            raw_payload=json.dumps(
                normalized_job.raw_payload,
                default=str,
            ),
            is_active=True,
            first_seen_at=now,
            last_seen_at=now,
        )

    # ------------------------------------------------------------------
    # Source listing update
    # ------------------------------------------------------------------

    def _update_listing(
        self,
        listing: JobSourceListing,
        normalized_job: NormalizedJob,
    ) -> None:
        """
        Update an existing source listing.

        last_seen_at records when our system observed the listing
        again.
        """

        listing.source_title = normalized_job.title

        listing.source_company_name = (
            normalized_job.company_name
        )

        listing.raw_description = normalized_job.description

        listing.raw_payload = json.dumps(
            normalized_job.raw_payload,
            default=str,
        )

        listing.original_url = normalized_job.application_url

        listing.is_active = True

        listing.last_seen_at = utc_now()

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_text(value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"\s+", " ", value)

        return value

    @staticmethod
    def _normalize_company_name(value: str) -> str:
        value = value.strip().lower()

        value = re.sub(
            r"[^a-z0-9]+",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()