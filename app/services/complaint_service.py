import random
import string
from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models.complaint import (
    Complaint,
    ComplaintAttachment,
    ComplaintRemark,
    Notification,
)
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintRemarkCreate,
    ComplaintAttachmentCreate,
)


class ComplaintService:
    """
    Service Layer encapsulating all business logic for Complaint Management.
    """

    @staticmethod
    def generate_ticket_number(transit_mode: Optional[str] = None) -> str:
        """
        Generates a unique human-readable ticket tracking number.
        Format: MT-[MODE]-[YEAR][MONTH]-[RANDOM4] e.g., MT-MET-202608-A7B2
        """
        now = datetime.utcnow()
        mode_prefix = "GEN"
        if transit_mode:
            clean_mode = transit_mode.strip().upper()
            if "METRO" in clean_mode:
                mode_prefix = "MET"
            elif "BUS" in clean_mode:
                mode_prefix = "BUS"
            elif "TRAIN" in clean_mode:
                mode_prefix = "TRN"
            else:
                mode_prefix = clean_mode[:3]

        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"MT-{mode_prefix}-{now.strftime('%Y%m')}-{random_suffix}"

    @classmethod
    def create_complaint(
        cls,
        db: Session,
        complaint_in: ComplaintCreate,
        citizen_id: Optional[UUID] = None,
    ) -> Complaint:
        """
        Creates a new complaint, saves any attachments, and logs the initial timeline remark.
        """
        effective_citizen_id = complaint_in.citizen_id or citizen_id
        transit_mode_val = complaint_in.transit_mode.lower() if complaint_in.transit_mode else "metro"
        priority_val = (complaint_in.priority or "medium").lower()
        language_val = (complaint_in.language or "en").lower()

        # Generate unique ticket number
        ticket_number = cls.generate_ticket_number(transit_mode_val)
        while db.query(Complaint).filter(Complaint.ticket_number == ticket_number).first():
            ticket_number = cls.generate_ticket_number(transit_mode_val)

        # Instantiate Complaint model
        db_complaint = Complaint(
            ticket_number=ticket_number,
            citizen_id=effective_citizen_id,
            department_id=complaint_in.department_id,
            category_id=complaint_in.category_id,
            transit_mode=transit_mode_val,
            form_data=complaint_in.form_data or {},
            title=complaint_in.title,
            description_original=complaint_in.description_original,
            language=language_val,
            priority=priority_val,
            status="submitted",
        )
        db.add(db_complaint)
        db.flush()  # Flush to generate db_complaint.id

        # Add attachments if provided in payload
        if complaint_in.attachments:
            for att in complaint_in.attachments:
                db_attachment = ComplaintAttachment(
                    complaint_id=db_complaint.id,
                    attachment_type=att.attachment_type.lower(),
                    file_name=att.file_name,
                    file_url=att.file_url,
                    mime_type=att.mime_type,
                    file_size=att.file_size,
                )
                db.add(db_attachment)

        # Log initial creation entry in Complaint Remarks (Timeline)
        initial_remark = ComplaintRemark(
            complaint_id=db_complaint.id,
            status="submitted",
            remarks="Complaint submitted successfully.",
            updated_by=None,
        )
        db.add(initial_remark)

        db.commit()
        db.refresh(db_complaint)
        return db_complaint

    @staticmethod
    def get_complaint_by_id(db: Session, complaint_id: UUID) -> Optional[Complaint]:
        """
        Fetches a complaint by UUID along with attachments and timeline remarks.
        """
        return (
            db.query(Complaint)
            .options(
                joinedload(Complaint.attachments),
                joinedload(Complaint.remarks),
                joinedload(Complaint.department),
                joinedload(Complaint.category),
            )
            .filter(Complaint.id == complaint_id)
            .first()
        )

    @staticmethod
    def get_complaint_by_ticket_number(db: Session, ticket_number: str) -> Optional[Complaint]:
        """
        Fetches a complaint by ticket tracking number (for public or direct lookup).
        """
        return (
            db.query(Complaint)
            .options(
                joinedload(Complaint.attachments),
                joinedload(Complaint.remarks),
            )
            .filter(Complaint.ticket_number == ticket_number)
            .first()
        )

    @staticmethod
    def get_timeline(db: Session, complaint_id: UUID) -> Optional[List[ComplaintRemark]]:
        """
        Fetches the chronological status & remarks history (Timeline) for a complaint.
        """
        db_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not db_complaint:
            return None
        return (
            db.query(ComplaintRemark)
            .filter(ComplaintRemark.complaint_id == complaint_id)
            .order_by(ComplaintRemark.created_at.asc())
            .all()
        )

    @staticmethod
    def get_complaints(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        citizen_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        category_id: Optional[UUID] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        transit_mode: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Complaint], int]:
        """
        Fetches paginated complaints with filtering and text search capabilities.
        """
        query = db.query(Complaint)

        # Filters
        if citizen_id:
            query = query.filter(Complaint.citizen_id == citizen_id)
        if department_id:
            query = query.filter(Complaint.department_id == department_id)
        if category_id:
            query = query.filter(Complaint.category_id == category_id)
        if status:
            query = query.filter(Complaint.status == status.lower())
        if priority:
            query = query.filter(Complaint.priority == priority.lower())
        if transit_mode:
            query = query.filter(Complaint.transit_mode == transit_mode.lower())

        # Keyword Search across Title, Description, and Ticket Number
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Complaint.title.ilike(search_pattern),
                    Complaint.description_original.ilike(search_pattern),
                    Complaint.ticket_number.ilike(search_pattern),
                )
            )

        total = query.count()
        complaints = (
            query.options(
                joinedload(Complaint.attachments),
                joinedload(Complaint.remarks),
            )
            .order_by(Complaint.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return complaints, total

    @staticmethod
    def update_complaint(
        db: Session,
        complaint_id: UUID,
        complaint_in: ComplaintUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Optional[Complaint]:
        """
        Updates complaint fields, handles status transitions (resolved/closed timestamps),
        and logs timeline remarks.
        """
        db_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not db_complaint:
            return None

        status_changed = False
        old_status = db_complaint.status

        # Update status if provided
        if complaint_in.status:
            new_status_val = complaint_in.status.lower()
            if db_complaint.status != new_status_val:
                db_complaint.status = new_status_val
                status_changed = True
                if new_status_val == "resolved":
                    db_complaint.resolved_at = datetime.utcnow()
                elif new_status_val == "closed":
                    db_complaint.closed_at = datetime.utcnow()

        # Update other fields
        if complaint_in.priority:
            db_complaint.priority = complaint_in.priority.lower()
        if complaint_in.department_id is not None:
            db_complaint.department_id = complaint_in.department_id
        if complaint_in.category_id is not None:
            db_complaint.category_id = complaint_in.category_id
        if complaint_in.feedback_rating is not None:
            db_complaint.feedback_rating = complaint_in.feedback_rating
        if complaint_in.feedback_comments is not None:
            db_complaint.feedback_comments = complaint_in.feedback_comments

        # Add remark / timeline audit record if status changed or remarks provided
        if status_changed or complaint_in.remarks:
            remark_text = complaint_in.remarks or f"Status changed from {old_status} to {db_complaint.status}."
            timeline_entry = ComplaintRemark(
                complaint_id=db_complaint.id,
                status=db_complaint.status,
                remarks=remark_text,
                updated_by=updated_by,
            )
            db.add(timeline_entry)

        db.commit()
        db.refresh(db_complaint)
        return db_complaint

    @staticmethod
    def add_remark(
        db: Session,
        complaint_id: UUID,
        remark_in: ComplaintRemarkCreate,
        updated_by: Optional[UUID] = None,
    ) -> Optional[ComplaintRemark]:
        """
        Adds a standalone timeline remark to a complaint.
        """
        db_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not db_complaint:
            return None

        status_val = remark_in.status.lower() if remark_in.status else db_complaint.status

        remark = ComplaintRemark(
            complaint_id=complaint_id,
            status=status_val,
            remarks=remark_in.remarks,
            updated_by=updated_by,
        )
        db.add(remark)
        db.commit()
        db.refresh(remark)
        return remark

    @staticmethod
    def add_attachment(
        db: Session,
        complaint_id: UUID,
        attachment_in: ComplaintAttachmentCreate,
    ) -> Optional[ComplaintAttachment]:
        """
        Attaches an uploaded file record to a complaint.
        """
        db_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not db_complaint:
            return None

        attachment = ComplaintAttachment(
            complaint_id=complaint_id,
            attachment_type=attachment_in.attachment_type.lower(),
            file_name=attachment_in.file_name,
            file_url=attachment_in.file_url,
            mime_type=attachment_in.mime_type,
            file_size=attachment_in.file_size,
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment

    @staticmethod
    def delete_complaint(db: Session, complaint_id: UUID) -> bool:
        """
        Deletes a complaint and cascades associated records.
        """
        db_complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not db_complaint:
            return False

        db.delete(db_complaint)
        db.commit()
        return True
