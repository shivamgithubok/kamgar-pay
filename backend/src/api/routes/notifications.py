from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.database.models import User
from src.db.session import get_db
from src.schemas.notification import NotificationListResponse, NotificationResponse
from src.services.notifications import (
    delete_notification,
    get_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
@router.get("/", response_model=NotificationListResponse)
def get_notifications_route(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    return get_user_notifications(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
    )


@router.patch("/read-all")
def mark_all_notifications_read_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = mark_all_notifications_read(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
    )
    return {"message": "All notifications marked as read", "count": count}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read_route(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    notif = mark_notification_read(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        notification_id=notification_id,
    )
    from src.services.notifications import to_notification_response
    return to_notification_response(notif)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification_route(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    delete_notification(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        notification_id=notification_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
