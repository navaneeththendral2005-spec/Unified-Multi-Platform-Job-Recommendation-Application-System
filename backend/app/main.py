from fastapi import FastAPI
from sqlalchemy import text

from app.database.connection import engine

# Import models so SQLAlchemy registers them
import app.models
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.job import Job
from app.models.resume import Resume
from app.models.user_skill import UserSkill
from app.models.resume_analysis import ResumeAnalysis
from app.models.user_preference import UserPreference
from app.models.skill import Skill
from app.models.job_skill import JobSkill
from app.models.skill_alias import SkillAlias

from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api import job
from app.api.recommendation import router as recommendation_router
from app.api.resume import router as resume_router
from app.api.user_preference import router as user_preference_router
from app.api.application import router as application_router
from app.api.notification import router as notification_router


app = FastAPI(
    title="AI Job Recommendation System",
    description="AI-powered Job and Internship Recommendation Platform",
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(job.router)
app.include_router(recommendation_router)
app.include_router(resume_router)
app.include_router(user_preference_router)
app.include_router(application_router)
app.include_router(notification_router)


@app.get("/")
def root():
    return {
        "message": "AI Job Recommendation System Backend is Running 🚀"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/database-test")
def database_test():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "database": "connected successfully ✅"
        }

    except Exception as error:
        return {
            "database": "connection failed ❌",
            "error": str(error),
        }