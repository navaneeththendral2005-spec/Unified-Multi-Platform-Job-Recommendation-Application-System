from app.recommendation.recommendation_service import (
    calculate_skill_match,
    recommend_jobs,
)


def test_perfect_skill_match():
    user_skills = [
        "Python",
        "FastAPI",
        "PostgreSQL",
    ]

    job_skills = [
        "Python",
        "FastAPI",
        "PostgreSQL",
    ]

    result = calculate_skill_match(
        user_skills=user_skills,
        job_skills=job_skills,
    )

    assert result == 100.0


def test_partial_skill_match():
    user_skills = [
        "Python",
        "FastAPI",
    ]

    job_skills = [
        "Python",
        "FastAPI",
        "PostgreSQL",
        "Docker",
    ]

    result = calculate_skill_match(
        user_skills=user_skills,
        job_skills=job_skills,
    )

    assert result == 50.0


def test_no_skill_match():
    user_skills = [
        "Python",
        "FastAPI",
    ]

    job_skills = [
        "Java",
        "Spring Boot",
        "MongoDB",
    ]

    result = calculate_skill_match(
        user_skills=user_skills,
        job_skills=job_skills,
    )

    assert result == 0.0


def test_case_insensitive_skill_match():
    user_skills = [
        "python",
        "FASTAPI",
    ]

    job_skills = [
        "Python",
        "FastAPI",
    ]

    result = calculate_skill_match(
        user_skills=user_skills,
        job_skills=job_skills,
    )

    assert result == 100.0


def test_empty_job_skills():
    user_skills = [
        "Python",
        "FastAPI",
    ]

    job_skills = []

    result = calculate_skill_match(
        user_skills=user_skills,
        job_skills=job_skills,
    )

    assert result == 0


def test_recommend_jobs_ranks_best_match_first():
    user_skills = [
        "Python",
        "FastAPI",
        "React",
        "Machine Learning",
    ]

    jobs = [
        {
            "title": "Backend Developer",
            "required_skills": [
                "Python",
                "FastAPI",
                "PostgreSQL",
            ],
        },
        {
            "title": "Frontend Developer",
            "required_skills": [
                "React",
                "JavaScript",
                "CSS",
            ],
        },
        {
            "title": "AI Engineer",
            "required_skills": [
                "Python",
                "Machine Learning",
            ],
        },
    ]

    recommendations = recommend_jobs(
        user_skills=user_skills,
        jobs=jobs,
    )

    assert recommendations[0]["job"]["title"] == "AI Engineer"
    assert recommendations[0]["match_score"] == 100.0


def test_recommend_jobs_returns_all_jobs():
    user_skills = [
        "Python",
    ]

    jobs = [
        {
            "title": "Python Developer",
            "required_skills": [
                "Python",
            ],
        },
        {
            "title": "Java Developer",
            "required_skills": [
                "Java",
            ],
        },
        {
            "title": "Frontend Developer",
            "required_skills": [
                "React",
            ],
        },
    ]

    recommendations = recommend_jobs(
        user_skills=user_skills,
        jobs=jobs,
    )

    assert len(recommendations) == 3