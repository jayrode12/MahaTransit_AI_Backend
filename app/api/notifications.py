from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_authenticated_user_id, get_current_user
from app.db.session import get_db
from app.models.complaint import Notification
from app.schemas.complaint import (
    NotificationCreate,
    NotificationListResponse,
    NotificationResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Get notifications for current user",
)
def get_my_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: UUID = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db),
):
    """
    Fetch all notifications for the currently logged-in citizen or officer.
    """
    skip = (page - 1) * limit
    items, total = NotificationService.get_user_notifications(
        db=db,
        user_id=user_id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )
    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .count()
    )
    return {
        "items": items,
        "total": total,
        "unread_count": unread_count,
    }


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new notification",
)
def create_notification(
    notification_in: NotificationCreate,
    _current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates an in-app notification for a user.
    """
    return NotificationService.create_notification(db=db, notification_in=notification_in)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark single notification as read",
)
def mark_notification_read(
    notification_id: UUID,
    _user_id: UUID = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db),
):
    """
    Marks a single notification as read.
    """
    notification = NotificationService.mark_as_read(db=db, notification_id=notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    return notification


@router.patch(
    "/read-all",
    summary="Mark all user notifications as read",
)
def mark_all_notifications_read(
    user_id: UUID = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db),
):
    """
    Marks all notifications for the current user as read.
    """
    updated_count = NotificationService.mark_all_as_read(db=db, user_id=user_id)
    return {
        "message": f"{updated_count} notifications marked as read.",
        "updated_count": updated_count,
    }
