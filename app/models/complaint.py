import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.base import Base


class Department(Base):
    """Department entity (Metro, BEST, Railway authorities)"""
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    complaints = relationship("Complaint", back_populates="department")
    categories = relationship("ComplaintCategory", back_populates="department")


class ComplaintCategory(Base):
    """Complaint Category entity linked to departments"""
    __tablename__ = "complaint_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    category_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    department = relationship("Department", back_populates="categories")
    complaints = relationship("Complaint", back_populates="category")


class Complaint(Base):
    """
    Core Complaints entity matching existing Supabase complaints table schema.
    """
    __tablename__ = "complaints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String(30), unique=True, index=True, nullable=False)
    citizen_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("complaint_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    transit_mode = Column(String(5), nullable=False, index=True)  # metro, bus, train
    form_data = Column(JSONB, nullable=True)  # route, bus/train number, coach, station details
    title = Column(String(255), nullable=False)
    description_original = Column(Text, nullable=False)
    description_english = Column(Text, nullable=True)
    language = Column(String(2), default="en", nullable=True)  # en, hi, mr
    
    priority = Column(String(8), default="medium", nullable=True)  # low, medium, high, critical
    status = Column(String(11), default="submitted", nullable=True)  # submitted, assigned, accepted, in_progress, resolved, closed, rejected
    
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    feedback_rating = Column(Integer, nullable=True)
    feedback_comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # Relationships
    department = relationship("Department", back_populates="complaints")
    category = relationship("ComplaintCategory", back_populates="complaints")
    attachments = relationship("ComplaintAttachment", back_populates="complaint", cascade="all, delete-orphan")
    remarks = relationship("ComplaintRemark", back_populates="complaint", cascade="all, delete-orphan", order_by="ComplaintRemark.created_at.desc()")
    notifications = relationship("Notification", back_populates="complaint")


class ComplaintAttachment(Base):
    """
    Complaint Attachments matching Supabase complaint_attachments table.
    """
    __tablename__ = "complaint_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    attachment_type = Column(String(8), nullable=False)  # image, audio, video, document
    file_name = Column(String(255), nullable=False)
    file_url = Column(Text, nullable=False)
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now(), nullable=True)

    complaint = relationship("Complaint", back_populates="attachments")


class ComplaintRemark(Base):
    """
    Complaint Remarks / Timeline matching Supabase complaint_remarks table.
    """
    __tablename__ = "complaint_remarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(11), nullable=True)
    remarks = Column(Text, nullable=True)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)

    complaint = relationship("Complaint", back_populates="remarks")


class Notification(Base):
    """
    Notifications matching Supabase notifications table.
    """
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_type = Column(String(7), nullable=False)  # citizen, admin
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True, index=True)
    type = Column(String(50), nullable=True)  # STATUS_UPDATE, ASSIGNED, etc.
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=True)

    complaint = relationship("Complaint", back_populates="notifications")
