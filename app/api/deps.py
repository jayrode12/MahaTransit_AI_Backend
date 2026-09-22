from typing import List, Optional
from uuid import UUID
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.citizen import Citizen
from app.models.admin import Admin
from app.core.supabase import supabase_client


def get_authenticated_user_id(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
) -> UUID:
    """
    Extracts the authenticated Supabase user ID from Authorization Bearer token or X-User-Id header.
    """
    if x_user_id:
        try:
            return UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID header",
            )

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if supabase_client:
            try:
                user_res = supabase_client.auth.get_user(token)
                if user_res and user_res.user:
                    return UUID(user_res.user.id)
            except Exception:
                pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide a valid Supabase session or user ID.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_citizen(
    user_id: UUID = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db),
) -> Citizen:
    """
    Resolves the active Citizen entity.
    """
    citizen = db.query(Citizen).filter(Citizen.id == user_id, Citizen.is_active == True).first()
    if not citizen:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Citizen account not found or deactivated.",
        )
    return citizen


def get_current_admin(
    user_id: UUID = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db),
) -> Admin:
    """
    Resolves the active Admin / Official entity.
    """
    admin = db.query(Admin).filter(Admin.id == user_id, Admin.is_active == True).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Official account not found or deactivated.",
        )
    return admin


def get_current_user(
    user_id: UUID = Depends(get_authenticated_user_id),
    db: Session = Depends(get_db),
):
    """
    Generic resolver for either Citizen or Admin.
    """
    citizen = db.query(Citizen).filter(Citizen.id == user_id, Citizen.is_active == True).first()
    if citizen:
        setattr(citizen, "user_type", "citizen")
        setattr(citizen, "current_role", "citizen")
        return citizen

    admin = db.query(Admin).filter(Admin.id == user_id, Admin.is_active == True).first()
    if admin:
        setattr(admin, "user_type", "admin")
        setattr(admin, "current_role", admin.role)
        return admin

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User account not found or deactivated.",
    )


def require_roles(allowed_roles: List[str]):
    """
    RBAC dependency guard ensuring current admin role is within allowed roles.
    """
    def role_checker(current_admin: Admin = Depends(get_current_admin)) -> Admin:
        if current_admin.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}",
            )
        return current_admin

    return role_checker
