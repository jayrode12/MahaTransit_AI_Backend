from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    user_type: Optional[str] = Field("citizen", pattern="^(citizen|admin)$")


class AuthResponse(BaseModel):
    user_id: UUID
    user_type: str
    role: str
    full_name: str
    email: EmailStr
    preferred_language: Optional[str] = "en"
    message: str = "Authentication successful"


class MessageResponse(BaseModel):
    message: str
