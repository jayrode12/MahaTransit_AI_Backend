from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class AdminProfileResponse(BaseModel):
    id: UUID
    department_id: Optional[UUID] = None
    role: str
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminOfficerCreate(BaseModel):
    department_id: Optional[UUID] = None
    role: str = Field("complaint_officer", pattern="^(super_admin|department_admin|complaint_officer)$")
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    password: str = Field(..., min_length=6)
