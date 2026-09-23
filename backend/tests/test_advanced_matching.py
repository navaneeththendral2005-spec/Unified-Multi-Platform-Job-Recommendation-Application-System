from app.services.advanced_matching import (
    canonical_skill,
    score_candidate_job,
)


def test_skill_aliases_are_canonicalized():
    assert canonical_skill("Postgres") == "postgresql"
    assert canonical_skill("ReactJS") == "react"


def test_advanced_match_returns_explainable_breakdown():
    result = score_candidate_job(
        candidate_skills=["Python", "FastAPI", "Postgres"],
        required_skills=["Python", "FastAPI", "PostgreSQL"],
        preferred_roles=["Backend Developer"],
        preferred_locations=["Chennai"],
        job_title="Backend Developer",
        job_location="Chennai, India",
        candidate_experience_years=2,
        required_experience="2 years",
    )

    assert result.score > 80
    assert result.skill_score == 100.0
    assert result.role_score == 100.0
    assert result.location_score == 100.0
    assert result.experience_score == 100.0
    assert "postgresql" in result.matched_skills
    assert result.reasons
