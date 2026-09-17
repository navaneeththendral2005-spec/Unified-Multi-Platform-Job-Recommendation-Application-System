import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user_preference import UserPreference
from app.schemas.user_preference import UserPreferenceCreate
from app.services.security import verify_access_token


router = APIRouter(
    prefix="/preferences",
    tags=["User Preferences"]
)


@router.post("/")
def save_user_preferences(
    preferences: UserPreferenceCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token)
):

    existing_preferences = db.query(
        UserPreference
    ).filter(
        UserPreference.user_id == current_user_id
    ).first()

    if existing_preferences:

        existing_preferences.preferred_roles = json.dumps(
            preferences.preferred_roles
        )

        existing_preferences.preferred_locations = json.dumps(
            preferences.preferred_locations
        )

        existing_preferences.willing_to_relocate = (
            preferences.willing_to_relocate
        )

        existing_preferences.experience_level = (
            preferences.experience_level
        )

        user_preferences = existing_preferences

    else:

        user_preferences = UserPreference(

            user_id=current_user_id,

            preferred_roles=json.dumps(
                preferences.preferred_roles
            ),

            preferred_locations=json.dumps(
                preferences.preferred_locations
            ),

            willing_to_relocate=preferences.willing_to_relocate,

            experience_level=preferences.experience_level
        )

        db.add(user_preferences)

    db.commit()
    db.refresh(user_preferences)

    return {
        "message": "User preferences saved successfully",

        "preferences": {
            "preferred_roles": json.loads(
                user_preferences.preferred_roles
            ) if user_preferences.preferred_roles else [],

            "preferred_locations": json.loads(
                user_preferences.preferred_locations
            ) if user_preferences.preferred_locations else [],

            "willing_to_relocate": (
                user_preferences.willing_to_relocate
            ),

            "experience_level": (
                user_preferences.experience_level
            )
        }
    }