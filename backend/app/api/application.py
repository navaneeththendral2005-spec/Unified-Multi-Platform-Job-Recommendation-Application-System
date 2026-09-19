from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.application import (
    ApplicationCreate,
    ApplicationEventResponse,
    ApplicationLifecycleStatus,
    ApplicationListResponse,
    ApplicationResponse,
    ApplicationStatusHistoryResponse,
    ApplicationStatusUpdate,
    ApplicationSummaryResponse,
    ApplicationTimelineResponse,
)
from app.services.application_event_service import get_application_events
from app.services.application_service import (
    create_application,
    get_application_history,
    get_application_lifecycle,
    get_application_summary,
    get_user_application,
    get_user_applications_paginated,
    update_application_status,
)
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


@router.get(
    "/summary",
    response_model=ApplicationSummaryResponse,
)
def read_application_summary(
    source_platform: str | None = Query(default=None, max_length=100),
    company: str | None = Query(default=None, min_length=1, max_length=255),
    applied_from: datetime | None = None,
    applied_to: datetime | None = None,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token),
):
    try:
        return get_application_summary(
            db=db,
            user_id=current_user_id,
            source_platform=source_platform,
            company=company,
            applied_from=applied_from,
            applied_to=applied_to,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


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
    response_model=ApplicationListResponse,
)
def read_my_applications(
    status_filter: str | None = Query(default=None, alias="status", max_length=50),
    source_platform: str | None = Query(default=None, max_length=100),
    company: str | None = Query(default=None, min_length=1, max_length=255),
    applied_from: datetime | None = None,
    applied_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token),
):
    try:
        applications, total = get_user_applications_paginated(
            db=db,
            user_id=current_user_id,
            status_filter=status_filter,
            source_platform=source_platform,
            company=company,
            applied_from=applied_from,
            applied_to=applied_to,
            page=page,
            page_size=page_size,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    total_pages = ceil(total / page_size) if total else 0

    return {
        "items": applications,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1 and total > 0,
    }


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
    "/{application_id}/timeline",
    response_model=ApplicationTimelineResponse,
)
def read_application_timeline(
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

    history = get_application_history(
        db=db,
        user_id=current_user_id,
        application_id=application_id,
    ) or []
    events = get_application_events(
        db=db,
        user_id=current_user_id,
        application_id=application_id,
    ) or []

    return {
        "application": application,
        "history": history,
        "events": events,
    }


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
