from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.citizen import Citizen
from app.models.admin import Admin
from app.schemas.auth import LoginRequest, AuthResponse, MessageResponse
from app.core.supabase import supabase_client


class AuthService:
    """
    Business service managing authentication (Login & Logout) via Supabase Auth.
    """

    @staticmethod
    def login(db: Session, login_in: LoginRequest) -> AuthResponse:
        user_id = None
        user_type = login_in.user_type or "citizen"

        # Authenticate via Supabase Auth if client is available
        if supabase_client:
            try:
                auth_res = supabase_client.auth.sign_in_with_password({
                    "email": login_in.email,
                    "password": login_in.password,
                })
                if auth_res and auth_res.user:
                    user_id = auth_res.user.id
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password.",
                )

        # Query profile from database
        if user_type == "citizen":
            citizen = db.query(Citizen).filter(Citizen.email == login_in.email).first()
            if not citizen:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Citizen profile not found.",
                )
            if not citizen.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Citizen account is deactivated.",
                )
            return AuthResponse(
                user_id=citizen.id,
                user_type="citizen",
                role="citizen",
                full_name=citizen.full_name,
                email=citizen.email,
                preferred_language=citizen.preferred_language,
                message="Citizen login successful",
            )
        else:
            admin = db.query(Admin).filter(Admin.email == login_in.email).first()
            if not admin:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Official profile not found.",
                )
            if not admin.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Official account is deactivated.",
                )
            return AuthResponse(
                user_id=admin.id,
                user_type="admin",
                role=admin.role,
                full_name=admin.full_name,
                email=admin.email,
                message="Official login successful",
            )

    @staticmethod
    def logout() -> MessageResponse:
        if supabase_client:
            try:
                supabase_client.auth.sign_out()
            except Exception:
                pass
        return MessageResponse(message="Successfully logged out")
