from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.complaint import (
    NotificationCreate,
    NotificationResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new notification",
)
def create_notification(
    notification_in: NotificationCreate,
    db: Session = Depends(get_db),
):
    """
    Creates a new notification record for a citizen or officer.
    """
    return NotificationService.create_notification(db=db, notification_in=notification_in)


@router.get(
    "",
    summary="Get user notifications with unread filter and pagination",
)
def list_notifications(
    user_id: UUID = Query(..., description="UUID of the recipient user"),
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Retrieves notification history for a user (citizen or officer).
    """
    skip = (page - 1) * limit
    items, total = NotificationService.get_user_notifications(
        db=db,
        user_id=user_id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark a single notification as read",
)
def mark_notification_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Marks a specific notification as read.
    """
    updated = NotificationService.mark_as_read(db=db, notification_id=notification_id)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID '{notification_id}' not found.",
        )
    return updated


@router.patch(
    "/read-all",
    summary="Mark all user notifications as read",
)
def mark_all_notifications_as_read(
    user_id: UUID = Query(..., description="UUID of the recipient user"),
    db: Session = Depends(get_db),
):
    """
    Marks all unread notifications for a user as read.
    """
    count = NotificationService.mark_all_as_read(db=db, user_id=user_id)
    return {"message": "All notifications marked as read", "updated_count": count}
