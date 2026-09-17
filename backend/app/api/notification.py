from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.application_notification import ApplicationNotificationResponse
from app.services.application_notification_service import (
    get_user_notifications,
    mark_notification_read,
)
from app.services.security import verify_access_token


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=list[ApplicationNotificationResponse],
)
def read_my_notifications(
    unread_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token),
):
    return get_user_notifications(
        db=db,
        user_id=current_user_id,
        unread_only=unread_only,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=ApplicationNotificationResponse,
)
def read_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(verify_access_token),
):
    notification = mark_notification_read(
        db=db,
        user_id=current_user_id,
        notification_id=notification_id,
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return notification
