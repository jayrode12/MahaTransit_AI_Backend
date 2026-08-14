from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.complaint import Notification
from app.schemas.complaint import NotificationCreate


class NotificationService:
    """
    Service layer for managing citizen and officer notifications.
    """

    @staticmethod
    def create_notification(db: Session, notification_in: NotificationCreate) -> Notification:
        """
        Creates a new in-app notification record.
        Handles foreign key constraints with auth.users gracefully.
        """
        try:
            notification = Notification(
                user_type=notification_in.user_type,
                user_id=notification_in.user_id,
                complaint_id=notification_in.complaint_id,
                type=notification_in.type,
                title=notification_in.title,
                message=notification_in.message,
                is_read=False,
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return notification
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot create notification: User ID '{notification_in.user_id}' does not exist in auth.users or Complaint ID is invalid.",
            )

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: UUID,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Notification], int]:
        """
        Retrieves notifications for a specific user with optional unread filter and pagination.
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)  # noqa: E712

        total = query.count()
        notifications = (
            query.order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return notifications, total

    @staticmethod
    def mark_as_read(db: Session, notification_id: UUID) -> Optional[Notification]:
        """
        Marks a single notification as read.
        """
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return None
        notification.is_read = True
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: UUID) -> int:
        """
        Marks all unread notifications for a user as read.
        Returns the number of updated records.
        """
        updated_count = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .update({"is_read": True})
        )
        db.commit()
        return updated_count
