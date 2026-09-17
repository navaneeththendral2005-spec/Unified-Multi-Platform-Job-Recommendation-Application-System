from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.application import (
    ApplicationCreate,
    ApplicationLifecycleStatus,
    ApplicationResponse,
    ApplicationStatusHistoryResponse,
    ApplicationStatusUpdate,
    ApplicationEventResponse,
)
from app.services.application_service import (
    create_application,
    get_application_history,
    get_application_lifecycle,
    get_user_application,
    get_user_applications,
    update_application_status,
)
from app.services.application_event_service import get_application_events
from app.services.security import verify_access_token



router = APIRouter(
    prefix="/applications",
    tags=["Applications"],
)


@router.get(
    "/lifecycle",
    response_model=list[ApplicationLifecycleStatus],
)
def read_application_lifecycle():
    """Return the canonical application statuses and valid next transitions."""
    return get_application_lifecycle()


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_application(
    application: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token),
):
    try:
        return create_application(
            db=db,
            user_id=current_user_id,
            application=application,
        )
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.get(
    "",
    response_model=list[ApplicationResponse],
)
def read_my_applications(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token),
):
    return get_user_applications(
        db=db,
        user_id=current_user_id,
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
)
def read_my_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token),
):
    application = get_user_application(
        db=db,
        user_id=current_user_id,
        application_id=application_id,
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    return application


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
)
def change_application_status(
    application_id: int,
    update: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token),
):
    try:
        application = update_application_status(
            db=db,
            user_id=current_user_id,
            application_id=application_id,
            update=update,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    return application


@router.get(
    "/{application_id}/history",
    response_model=list[ApplicationStatusHistoryResponse],
)
def read_application_history(
    application_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token),
):
    history = get_application_history(
        db=db,
        user_id=current_user_id,
        application_id=application_id,
    )

    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    return history

@router.get(
    "/{application_id}/events",
    response_model=list[ApplicationEventResponse],
)
def read_application_events(
    application_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token),
):
    events = get_application_events(
        db=db,
        user_id=current_user_id,
        application_id=application_id,
    )

    if events is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    return events
