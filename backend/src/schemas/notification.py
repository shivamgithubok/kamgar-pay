from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NotificationCreatePayload(BaseModel):
    user_id: str
    worker_id: Optional[str] = None
    notification_type: str = Field(..., max_length=30)
    title: str = Field(..., max_length=150)
    message: str


class NotificationResponse(BaseModel):
    id: str
    organization_id: str
    user_id: str
    worker_id: Optional[str] = None
    worker_name: Optional[str] = None
    notification_type: str
    title: str
    message: str
    status: str
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int
    total: int
