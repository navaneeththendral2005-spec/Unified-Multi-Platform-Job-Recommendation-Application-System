from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.schemas.user import (
    UserRegister,
    UserResponse,
    UserLogin,
    TokenResponse
)

from app.services.auth_service import (
    get_user_by_email,
    create_user,
    verify_password
)

from app.services.security import (
    create_access_token,
    verify_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = get_user_by_email(
        db,
        user.email
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    new_user = create_user(
        db=db,
        name=user.name,
        email=user.email,
        password=user.password
    )

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = get_user_by_email(
        db,
        user.email
    )

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    password_valid = verify_password(
        user.password,
        existing_user.password_hash
    )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={
            "sub": str(existing_user.id),
            "email": existing_user.email
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_current_user(
    token_data: dict = Depends(verify_access_token)
):
    return {
        "message": "You are authenticated!",
        "user": token_data
    }