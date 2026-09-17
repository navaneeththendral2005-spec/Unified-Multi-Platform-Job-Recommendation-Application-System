from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.security import verify_access_token
from app.services.recommendation_service import (
    generate_user_recommendations
)


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/")
def get_my_recommendations(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token)
):
    """
    Generate personalized job recommendations
    for the currently authenticated user.
    """

    recommendations = generate_user_recommendations(
        db=db,
        user_id=current_user_id
    )

    if recommendations is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "User profile not found. "
                "Please create your profile first."
            )
        )

    if not recommendations:
        raise HTTPException(
            status_code=404,
            detail=(
                "No suitable job recommendations found."
            )
        )

    return {
        "total_recommendations": len(recommendations),

        "recommendations": [
            {
                "job_id": item["job"].id,
                "title": item["job"].title,
                "company": item["job"].company,
                "location": item["job"].location,

                "required_skills": item["required_skills"],

                "match_score": item["match_score"],
                "match_level": item["match_level"],

                "skill_match_percentage": (
                    item["skill_match_percentage"]
                ),

                "matched_skills": (
                    item["matched_skills"]
                ),

                "missing_skills": (
                    item["missing_skills"]
                ),

                "reasons": item["reasons"]
            }
            for item in recommendations
        ]
    }