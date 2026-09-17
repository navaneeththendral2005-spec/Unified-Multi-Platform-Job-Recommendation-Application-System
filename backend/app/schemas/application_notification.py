from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    application_id: int
    event_id: int
    channel: str
    notification_type: str
    recipient: str
    subject: str
    body: str
    delivery_status: str
    attempts: int
    last_attempt_at: datetime | None
    sent_at: datetime | None
    failed_at: datetime | None
    error_message: str | None
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime
