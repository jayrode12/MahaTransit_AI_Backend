from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


TransitModeType = Literal["metro", "bus", "train"]
ComplaintPriorityType = Literal["low", "medium", "high", "critical"]
ComplaintStatusType = Literal[
    "submitted", "assigned", "accepted", "in_progress", "resolved", "closed", "rejected"
]
AttachmentTypeLiteral = Literal["image", "audio", "video", "document"]
LanguageCodeType = Literal["en", "hi", "mr"]


# ---------------------------------------------------------
# Attachment Schemas
# ---------------------------------------------------------
class ComplaintAttachmentBase(BaseModel):
    attachment_type: AttachmentTypeLiteral = Field(..., description="image, audio, video, document")
    file_name: str = Field(..., max_length=255)
    file_url: str = Field(..., description="Supabase storage URL")
    mime_type: Optional[str] = Field(None, max_length=100)
    file_size: Optional[int] = None


class ComplaintAttachmentCreate(ComplaintAttachmentBase):
    pass


class ComplaintAttachmentResponse(ComplaintAttachmentBase):
    id: UUID
    complaint_id: UUID
    uploaded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Remark / Timeline Schemas
# ---------------------------------------------------------
class ComplaintRemarkBase(BaseModel):
    status: Optional[ComplaintStatusType] = None
    remarks: Optional[str] = None


class ComplaintRemarkCreate(BaseModel):
    status: Optional[ComplaintStatusType] = None
    remarks: str = Field(..., description="Officer or admin remarks")


class ComplaintRemarkResponse(ComplaintRemarkBase):
    id: UUID
    complaint_id: UUID
    updated_by: Optional[UUID] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Complaint Schemas
# ---------------------------------------------------------
class ComplaintBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description_original: str = Field(..., min_length=5)
    transit_mode: TransitModeType = Field("metro")
    department_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    form_data: Optional[Dict[str, Any]] = None
    language: Optional[LanguageCodeType] = "en"


class ComplaintCreate(ComplaintBase):
    citizen_id: Optional[UUID] = None
    priority: Optional[ComplaintPriorityType] = "medium"
    attachments: Optional[List[ComplaintAttachmentCreate]] = None


class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatusType] = None
    priority: Optional[ComplaintPriorityType] = None
    department_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    remarks: Optional[str] = None
    feedback_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_comments: Optional[str] = None


class ComplaintResponse(ComplaintBase):
    id: UUID
    ticket_number: str
    citizen_id: Optional[UUID] = None
    description_english: Optional[str] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "submitted"
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    feedback_rating: Optional[int] = None
    feedback_comments: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    attachments: List[ComplaintAttachmentResponse] = []
    remarks: List[ComplaintRemarkResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ComplaintListResponse(BaseModel):
    items: List[ComplaintResponse]
    total: int
    page: int
    limit: int
    pages: int
