from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# Allowed Literals
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
    attachment_type: AttachmentTypeLiteral = Field(..., description="File type: image, audio, video, document")
    file_name: str = Field(..., max_length=255)
    file_url: str = Field(..., description="Public Supabase storage URL")
    mime_type: Optional[str] = Field(None, max_length=100)
    file_size: Optional[int] = Field(None, description="Size in bytes")


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
    remarks: str = Field(..., description="Officer or admin resolution remarks")


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
    title: str = Field(..., min_length=3, max_length=255, description="Brief complaint summary")
    description_original: str = Field(..., min_length=5, description="Full complaint details in citizen's language")
    transit_mode: TransitModeType = Field("metro", description="metro, bus, or train")
    department_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    form_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Transit details like route, coach, stop")
    language: Optional[LanguageCodeType] = Field("en", description="Language code: en, hi, mr")


class ComplaintCreate(ComplaintBase):
    citizen_id: Optional[UUID] = None
    priority: Optional[ComplaintPriorityType] = Field("medium", description="low, medium, high, critical")
    attachments: Optional[List[ComplaintAttachmentCreate]] = []


class ComplaintUpdate(BaseModel):
    status: Optional[ComplaintStatusType] = Field(None, description="submitted, assigned, accepted, in_progress, resolved, closed, rejected")
    priority: Optional[ComplaintPriorityType] = Field(None, description="low, medium, high, critical")
    department_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    remarks: Optional[str] = Field(None, description="Optional remarks added when updating status")
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


# ---------------------------------------------------------
# Notification Schemas
# ---------------------------------------------------------
class NotificationCreate(BaseModel):
    user_type: Literal["citizen", "admin"] = "citizen"
    user_id: UUID
    complaint_id: Optional[UUID] = None
    type: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., max_length=150)
    message: str


class NotificationResponse(BaseModel):
    id: UUID
    user_type: str
    user_id: UUID
    complaint_id: Optional[UUID] = None
    type: Optional[str] = None
    title: str
    message: str
    is_read: bool
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
