from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user_profile import UserProfile
from app.schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse
)
from app.services.security import verify_access_token


router = APIRouter(
    prefix="/profile",
    tags=["User Profile"]
)


@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED
)
def create_profile(
    profile: ProfileCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token)
):
    existing_profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == current_user_id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists"
        )

    new_profile = UserProfile(
        user_id=current_user_id,
        **profile.model_dump()
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return new_profile


@router.get(
    "/me",
    response_model=ProfileResponse
)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token)
):
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == current_user_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return profile


@router.put(
    "",
    response_model=ProfileResponse
)
def update_profile(
    profile_data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token)
):
    profile = (
        db.query(UserProfile)
        .filter(UserProfile.user_id == current_user_id)
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile