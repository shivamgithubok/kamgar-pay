from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from src.database.models import Notification, User, Worker
from src.schemas.notification import NotificationListResponse, NotificationResponse


def create_notification(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    worker_id: Optional[str] = None,
) -> Notification:
    notif = Notification(
        organization_id=organization_id,
        user_id=user_id,
        worker_id=worker_id,
        notification_type=notification_type.strip(),
        title=title.strip(),
        message=message.strip(),
        status="unread",
        is_read=False,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def notify_organization_admins(
    db: Session,
    *,
    organization_id: str,
    notification_type: str,
    title: str,
    message: str,
    worker_id: Optional[str] = None,
) -> list[Notification]:
    admin_users = db.execute(
        select(User).where(
            User.organization_id == organization_id,
            User.role.in_(["organization_admin", "staff"]),
            User.is_active == True,
        )
    ).scalars().all()

    created_notifs: list[Notification] = []
    for admin in admin_users:
        notif = Notification(
            organization_id=organization_id,
            user_id=admin.id,
            worker_id=worker_id,
            notification_type=notification_type.strip(),
            title=title.strip(),
            message=message.strip(),
            status="unread",
            is_read=False,
        )
        db.add(notif)
        created_notifs.append(notif)

    if created_notifs:
        db.commit()
        for n in created_notifs:
            db.refresh(n)

    return created_notifs


def get_user_notifications(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    unread_only: bool = False,
    limit: int = 50,
) -> NotificationListResponse:
    query = (
        select(Notification)
        .options(selectinload(Notification.worker))
        .where(
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
        )
    )

    if unread_only:
        query = query.where(Notification.is_read == False)

    query = query.order_by(Notification.created_at.desc()).limit(limit)
    items_raw = db.execute(query).scalars().all()

    # Unread count
    unread_count = db.execute(
        select(Notification)
        .where(
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
    ).scalars().all()

    items = [to_notification_response(n) for n in items_raw]
    return NotificationListResponse(
        items=items,
        unread_count=len(unread_count),
        total=len(items),
    )


def mark_notification_read(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    notification_id: str,
) -> Notification:
    notif = db.execute(
        select(Notification).where(
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
            Notification.id == notification_id,
        )
    ).scalar_one_or_none()

    if notif is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    if not notif.is_read:
        notif.is_read = True
        notif.status = "read"
        notif.read_at = datetime.utcnow()
        db.add(notif)
        db.commit()
        db.refresh(notif)

    return notif


def mark_all_notifications_read(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
) -> int:
    now = datetime.utcnow()
    result = db.execute(
        update(Notification)
        .where(
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        .values(is_read=True, status="read", read_at=now)
    )
    db.commit()
    return result.rowcount


def delete_notification(
    db: Session,
    *,
    organization_id: str,
    user_id: str,
    notification_id: str,
) -> None:
    notif = db.execute(
        select(Notification).where(
            Notification.organization_id == organization_id,
            Notification.user_id == user_id,
            Notification.id == notification_id,
        )
    ).scalar_one_or_none()

    if notif is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    db.delete(notif)
    db.commit()


def to_notification_response(n: Notification) -> NotificationResponse:
    worker_name = None
    if n.worker:
        parts = [n.worker.first_name, n.worker.last_name]
        worker_name = " ".join(p for p in parts if p)

    return NotificationResponse(
        id=n.id,
        organization_id=n.organization_id,
        user_id=n.user_id,
        worker_id=n.worker_id,
        worker_name=worker_name,
        notification_type=n.notification_type,
        title=n.title,
        message=n.message,
        status=n.status,
        is_read=n.is_read,
        read_at=n.read_at,
        created_at=n.created_at,
    )
