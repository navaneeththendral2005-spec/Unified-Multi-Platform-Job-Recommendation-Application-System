"""Seed a diverse set of demo jobs for CareerAI.

This script is intentionally idempotent: running it repeatedly will not
create duplicate demo jobs for the same title/company/location combination.

The records are demo/test opportunities, not verified live vacancies.
Their application URLs intentionally point to example.com so the project
can exercise the application flow without pretending that a real vacancy
exists.

Run from the backend directory:
    python scripts/seed_demo_jobs.py
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from pathlib import Path

# Make `app` importable when this file is executed directly.
BACKEND_DIR = Path(__file__).resolve().parents[1]

from sqlalchemy import select

from app.database.connection import SessionLocal
from app.models.company import Company
from app.models.job import Job
from app.models.job_source import JobSource
from app.models.job_source_listing import JobSourceListing
from app.services.job_service import create_job
from app.services.job_source_service import JobSourceService
from app.services.skill_service import get_or_create_skill


DEMO_JOBS = [
    # ------------------------------------------------------------------
    # AI / MACHINE LEARNING
    # ------------------------------------------------------------------
    {
        "title": "AI Engineer",
        "company": "NovaMind Technologies",
        "location": "Bangalore",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Python", "Machine Learning", "TensorFlow", "SQL"],
        "description": "Build and evaluate machine learning services, data pipelines, and AI features for production applications.",
        "source": "linkedin",
    },
    {
        "title": "NLP Engineer",
        "company": "LexiAI Labs",
        "location": "Hyderabad",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["Python", "NLP", "PyTorch", "Transformers"],
        "description": "Develop natural language processing pipelines for classification, search, summarization, and conversational AI.",
        "source": "wellfound",
    },
    {
        "title": "Computer Vision Engineer",
        "company": "VisionForge Systems",
        "location": "Chennai",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Python", "OpenCV", "Computer Vision", "YOLOv8"],
        "description": "Create computer vision pipelines for image analysis, object detection, and real-time video processing.",
        "source": "naukri",
    },
    {
        "title": "AI Research Intern",
        "company": "Cognitive Research Hub",
        "location": "Remote",
        "job_type": "Internship",
        "experience_required": "Student / Entry-level",
        "skills": ["Python", "Machine Learning", "PyTorch", "Research"],
        "description": "Assist with experiments, model evaluation, literature reviews, and prototype development for applied AI research.",
        "source": "internshala",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "DataNova Analytics",
        "location": "Pune",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["Python", "Machine Learning", "Scikit-Learn", "Pandas"],
        "description": "Train and deploy predictive models and collaborate with data teams to turn business problems into ML solutions.",
        "source": "indeed",
    },

    # ------------------------------------------------------------------
    # SOFTWARE / BACKEND / FULL STACK
    # ------------------------------------------------------------------
    {
        "title": "Backend Developer",
        "company": "CloudPeak Software",
        "location": "Chennai",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Python", "FastAPI", "PostgreSQL", "REST API"],
        "description": "Build scalable backend APIs and data services using Python, FastAPI, PostgreSQL, and modern testing practices.",
        "source": "naukri",
    },
    {
        "title": "Full Stack Developer",
        "company": "BrightStack Solutions",
        "location": "Bangalore",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["React", "JavaScript", "Python", "FastAPI", "PostgreSQL"],
        "description": "Develop end-to-end web applications across React interfaces, backend APIs, authentication, and databases.",
        "source": "linkedin",
    },
    {
        "title": "Software Engineer",
        "company": "Orbit Systems",
        "location": "Hyderabad",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Python", "Java", "SQL", "Git"],
        "description": "Implement reliable software components, write automated tests, and collaborate with engineering teams on product features.",
        "source": "indeed",
    },
    {
        "title": "Python Developer",
        "company": "TechBridge Innovations",
        "location": "Remote",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Python", "Django", "REST API", "PostgreSQL"],
        "description": "Develop and maintain Python web services, integrations, background jobs, and database-backed features.",
        "source": "wellfound",
    },
    {
        "title": "Java Backend Engineer",
        "company": "Enterprise Grid Technologies",
        "location": "Mumbai",
        "job_type": "Full-time",
        "experience_required": "2-4 years",
        "skills": ["Java", "Spring Boot", "SQL", "REST API"],
        "description": "Build enterprise backend services with Spring Boot, relational databases, APIs, and automated testing.",
        "source": "naukri",
    },

    # ------------------------------------------------------------------
    # FRONTEND / WEB
    # ------------------------------------------------------------------
    {
        "title": "Frontend Developer",
        "company": "PixelCraft Digital",
        "location": "Chennai",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["React", "JavaScript", "HTML", "CSS"],
        "description": "Create responsive and accessible web interfaces with React, JavaScript, HTML, and CSS.",
        "source": "internshala",
    },
    {
        "title": "React Developer",
        "company": "WebSphere Labs",
        "location": "Pune",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["React", "JavaScript", "TypeScript", "CSS"],
        "description": "Build reusable React components, integrate APIs, and improve frontend performance and user experience.",
        "source": "linkedin",
    },
    {
        "title": "Web Developer Intern",
        "company": "LaunchPad Technologies",
        "location": "Coimbatore",
        "job_type": "Internship",
        "experience_required": "Student / Entry-level",
        "skills": ["HTML", "CSS", "JavaScript", "Git"],
        "description": "Support the development of responsive web pages and learn modern frontend development workflows.",
        "source": "internshala",
    },
    {
        "title": "UI Engineer",
        "company": "InterfaceWorks",
        "location": "Remote",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["React", "TypeScript", "JavaScript", "CSS"],
        "description": "Translate product designs into polished, reusable interface components with strong attention to accessibility.",
        "source": "wellfound",
    },

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------
    {
        "title": "Data Analyst",
        "company": "InsightArc Consulting",
        "location": "Hyderabad",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Python", "SQL", "Pandas", "Power BI"],
        "description": "Analyze business datasets, build dashboards, and communicate actionable findings to product and operations teams.",
        "source": "indeed",
    },
    {
        "title": "Junior Data Scientist",
        "company": "QuantLeaf Analytics",
        "location": "Bangalore",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Python", "Machine Learning", "Pandas", "Scikit-Learn"],
        "description": "Prepare datasets, build predictive models, evaluate experiments, and communicate data-driven insights.",
        "source": "naukri",
    },
    {
        "title": "Business Intelligence Analyst",
        "company": "MarketPulse India",
        "location": "Mumbai",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["SQL", "Power BI", "Excel", "Data Analysis"],
        "description": "Develop business dashboards and reporting solutions that help teams understand performance and trends.",
        "source": "linkedin",
    },
    {
        "title": "Data Engineering Intern",
        "company": "StreamData Technologies",
        "location": "Chennai",
        "job_type": "Internship",
        "experience_required": "Student / Entry-level",
        "skills": ["Python", "SQL", "ETL", "PostgreSQL"],
        "description": "Assist with data ingestion, transformation, validation, and warehouse-oriented engineering tasks.",
        "source": "internshala",
    },

    # ------------------------------------------------------------------
    # CLOUD / DEVOPS
    # ------------------------------------------------------------------
    {
        "title": "Cloud Engineer",
        "company": "SkyRoute Technologies",
        "location": "Bangalore",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["AWS", "Docker", "Linux", "Python"],
        "description": "Support cloud infrastructure, containerized workloads, monitoring, and automation for production services.",
        "source": "indeed",
    },
    {
        "title": "DevOps Engineer",
        "company": "DeployOps Systems",
        "location": "Pune",
        "job_type": "Full-time",
        "experience_required": "2-4 years",
        "skills": ["Docker", "Kubernetes", "AWS", "CI/CD"],
        "description": "Build deployment pipelines, manage container platforms, and improve reliability and delivery automation.",
        "source": "linkedin",
    },
    {
        "title": "Site Reliability Engineer",
        "company": "ScaleGrid Technologies",
        "location": "Hyderabad",
        "job_type": "Full-time",
        "experience_required": "2-4 years",
        "skills": ["Linux", "Kubernetes", "Docker", "Python"],
        "description": "Improve system reliability through automation, observability, incident response, and scalable infrastructure practices.",
        "source": "wellfound",
    },
    {
        "title": "Cloud Support Associate",
        "company": "NimbusWorks",
        "location": "Remote",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["AWS", "Linux", "Networking", "Python"],
        "description": "Help customers troubleshoot cloud environments, networking issues, deployments, and infrastructure configurations.",
        "source": "naukri",
    },

    # ------------------------------------------------------------------
    # CYBERSECURITY
    # ------------------------------------------------------------------
    {
        "title": "Cybersecurity Analyst",
        "company": "SecureSphere Labs",
        "location": "Chennai",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Cybersecurity", "Linux", "Networking", "Python"],
        "description": "Monitor security events, investigate alerts, and assist with vulnerability and security operations workflows.",
        "source": "naukri",
    },
    {
        "title": "SOC Analyst",
        "company": "ShieldNet Security",
        "location": "Bangalore",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Cybersecurity", "SIEM", "Networking", "Linux"],
        "description": "Analyze security alerts, investigate suspicious activity, and document incidents in a security operations center.",
        "source": "indeed",
    },
    {
        "title": "Application Security Intern",
        "company": "AppGuard Technologies",
        "location": "Remote",
        "job_type": "Internship",
        "experience_required": "Student / Entry-level",
        "skills": ["Cybersecurity", "Python", "Git", "Web Security"],
        "description": "Assist with application security testing, vulnerability documentation, and secure development practices.",
        "source": "internshala",
    },

    # ------------------------------------------------------------------
    # MOBILE
    # ------------------------------------------------------------------
    {
        "title": "Android Developer",
        "company": "MobileFirst Labs",
        "location": "Bangalore",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["Android", "Kotlin", "Java", "Git"],
        "description": "Develop Android applications, integrate APIs, and collaborate with designers and backend engineers.",
        "source": "linkedin",
    },
    {
        "title": "Flutter Developer",
        "company": "AppOrbit Solutions",
        "location": "Chennai",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Flutter", "Dart", "REST API", "Git"],
        "description": "Build cross-platform mobile experiences with Flutter and integrate them with backend services.",
        "source": "naukri",
    },
    {
        "title": "Mobile App Intern",
        "company": "PocketApps Studio",
        "location": "Mumbai",
        "job_type": "Internship",
        "experience_required": "Student / Entry-level",
        "skills": ["Flutter", "Dart", "Git"],
        "description": "Work with the mobile team on UI implementation, API integration, testing, and app improvements.",
        "source": "internshala",
    },

    # ------------------------------------------------------------------
    # UI / UX / PRODUCT
    # ------------------------------------------------------------------
    {
        "title": "UI/UX Designer",
        "company": "DesignLoop Studio",
        "location": "Mumbai",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["Figma", "UI/UX", "Prototyping", "User Research"],
        "description": "Design intuitive digital experiences, prototypes, and user flows in collaboration with product and engineering teams.",
        "source": "wellfound",
    },
    {
        "title": "Product Designer",
        "company": "ProductCraft Labs",
        "location": "Bangalore",
        "job_type": "Full-time",
        "experience_required": "2-4 years",
        "skills": ["Figma", "UI/UX", "Prototyping", "Product Design"],
        "description": "Own product design from discovery and wireframes through high-fidelity prototypes and design handoff.",
        "source": "linkedin",
    },
    {
        "title": "UX Research Intern",
        "company": "HumanFirst Design",
        "location": "Remote",
        "job_type": "Internship",
        "experience_required": "Student / Entry-level",
        "skills": ["User Research", "UI/UX", "Figma"],
        "description": "Support user interviews, usability studies, synthesis, and research documentation for digital products.",
        "source": "internshala",
    },

    # ------------------------------------------------------------------
    # QA / TESTING
    # ------------------------------------------------------------------
    {
        "title": "QA Automation Engineer",
        "company": "QualityStack Technologies",
        "location": "Pune",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["Python", "Selenium", "Automation Testing", "Git"],
        "description": "Create automated test suites, maintain regression coverage, and work with developers to improve software quality.",
        "source": "indeed",
    },
    {
        "title": "Software Test Engineer",
        "company": "VerifySoft Solutions",
        "location": "Hyderabad",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Testing", "Selenium", "SQL", "Git"],
        "description": "Design test cases, execute functional testing, validate releases, and document defects and regression results.",
        "source": "naukri",
    },
    {
        "title": "QA Intern",
        "company": "TestPilot Labs",
        "location": "Chennai",
        "job_type": "Internship",
        "experience_required": "Student / Entry-level",
        "skills": ["Testing", "Python", "Git"],
        "description": "Learn software testing workflows while assisting with test execution, bug reporting, and regression checks.",
        "source": "internshala",
    },

    # ------------------------------------------------------------------
    # BUSINESS / PRODUCT
    # ------------------------------------------------------------------
    {
        "title": "Business Analyst",
        "company": "GrowthBridge Consulting",
        "location": "Chennai",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Business Analysis", "SQL", "Excel", "Data Analysis"],
        "description": "Gather requirements, analyze business processes, and translate stakeholder needs into actionable product requirements.",
        "source": "linkedin",
    },
    {
        "title": "Product Analyst",
        "company": "MetricWorks",
        "location": "Bangalore",
        "job_type": "Full-time",
        "experience_required": "1-3 years",
        "skills": ["SQL", "Data Analysis", "Python", "Product Analytics"],
        "description": "Analyze product usage, build metrics, and support product decisions with quantitative insights.",
        "source": "indeed",
    },
    {
        "title": "Associate Product Manager",
        "company": "NextWave Products",
        "location": "Hyderabad",
        "job_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Product Management", "Agile", "Data Analysis", "User Research"],
        "description": "Support product discovery, roadmap planning, user feedback analysis, and cross-functional delivery.",
        "source": "wellfound",
    },

    # ------------------------------------------------------------------
    # GENERAL SOFTWARE / REMOTE
    # ------------------------------------------------------------------
    {
        "title": "API Integration Engineer",
        "company": "ConnectFlow Technologies",
        "location": "Remote",
        "job_type": "Contract",
        "experience_required": "1-3 years",
        "skills": ["Python", "REST API", "JavaScript", "PostgreSQL"],
        "description": "Build third-party integrations, API clients, webhooks, and data synchronization workflows for SaaS products.",
        "source": "wellfound",
    },
    {
        "title": "Junior Software Engineer",
        "company": "CodeHarbor Systems",
        "location": "Coimbatore",
        "job_type": "Full-time",
        "experience_required": "0-1 years",
        "skills": ["Python", "JavaScript", "SQL", "Git"],
        "description": "Join a product engineering team to implement features, fix defects, write tests, and learn production development practices.",
        "source": "naukri",
    },
]


def normalize_company_name(name: str) -> str:
    value = name.strip().lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def get_or_create_company(db, name: str) -> Company:
    normalized = normalize_company_name(name)
    company = db.scalar(
        select(Company).where(
            Company.normalized_name == normalized
        )
    )

    if company:
        return company

    company = Company(
        name=name,
        normalized_name=normalized,
        industry="Technology",
        description=f"Demo company profile for the CareerAI development dataset: {name}.",
    )
    db.add(company)
    db.flush()
    return company


def get_or_create_source(db, source_name: str) -> JobSource:
    source_service = JobSourceService(db)
    source = source_service.get_source(source_name)

    if source is None:
        source_service.initialize_catalog()
        source = source_service.get_source(source_name)

    if source is None:
        raise RuntimeError(f"Unable to initialize job source: {source_name}")

    return source


def main() -> None:
    db = SessionLocal()
    created = 0
    skipped = 0

    try:
        # Register the project's five supported source definitions.
        JobSourceService(db).initialize_catalog()

        # Ensure every skill used by the demo jobs exists in the
        # central registry before JobService performs extraction.
        all_skills = sorted(
            {
                skill
                for item in DEMO_JOBS
                for skill in item["skills"]
            },
            key=str.casefold,
        )

        for skill_name in all_skills:
            get_or_create_skill(db, skill_name)
        db.commit()

        now = datetime.now()

        for index, item in enumerate(DEMO_JOBS, start=1):
            existing = db.scalar(
                select(Job).where(
                    Job.title == item["title"],
                    Job.company == item["company"],
                    Job.location == item["location"],
                )
            )

            if existing:
                skipped += 1
                continue

            slug = slugify(
                f"{item['company']}-{item['title']}-{item['location']}"
            )

            # The application URL is deliberately a demo endpoint.
            # It exercises the UI's external-link/application flow
            # without representing a real vacancy.
            application_url = (
                f"https://example.com/careerai-demo/apply/{slug}"
            )

            job_payload = type(
                "SeedJob",
                (),
                {
                    "title": item["title"],
                    "company": item["company"],
                    "description": item["description"],
                    "required_skills": ", ".join(item["skills"]),
                    "location": item["location"],
                    "job_type": item["job_type"],
                    "experience_required": item["experience_required"],
                    "application_link": application_url,
                },
            )()

            # create_job expects a JobCreate-like object and also creates
            # the structured JobSkill relationships used by recommendations.
            job = create_job(db, job_payload)

            company = get_or_create_company(db, item["company"])
            job.company_id = company.id
            job.company = company.name

            source = get_or_create_source(db, item["source"])
            external_id = f"careerai-demo-{index:03d}-{slug}"

            listing_exists = db.scalar(
                select(JobSourceListing).where(
                    JobSourceListing.source_id == source.id,
                    JobSourceListing.external_job_id == external_id,
                )
            )

            if listing_exists is None:
                listing = JobSourceListing(
                    job_id=job.id,
                    source_id=source.id,
                    external_job_id=external_id,
                    original_url=application_url,
                    source_title=item["title"],
                    source_company_name=item["company"],
                    raw_description=item["description"],
                    raw_payload=(
                        '{"demo": true, "dataset": "careerai-demo-jobs"}'
                    ),
                    is_active=True,
                    first_seen_at=now,
                    last_seen_at=now,
                    created_at=now,
                    updated_at=now,
                )
                db.add(listing)

            # Spread demo posting dates across the last two weeks so the
            # UI has meaningful-looking posted-at values during testing.
            job.posted_at = now - timedelta(days=(index % 14))
            db.commit()
            created += 1

        print("CareerAI demo job seed completed.")
        print(f"Created: {created}")
        print(f"Skipped existing: {skipped}")
        print(f"Total demo records in dataset: {len(DEMO_JOBS)}")
        print("Note: application URLs are demo example.com endpoints.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
