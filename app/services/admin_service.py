import uuid
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.schemas.admin import AdminProfileResponse, AdminOfficerCreate
from app.core.supabase import supabase_admin


class AdminService:
    """
    Business service managing Officials, Department Admins, and Super Admin provisioning.
    """

    @staticmethod
    def get_profile(admin: Admin) -> AdminProfileResponse:
        return AdminProfileResponse.model_validate(admin)

    @staticmethod
    def create_officer(db: Session, officer_in: AdminOfficerCreate) -> AdminProfileResponse:
        # Check email uniqueness
        if db.query(Admin).filter(Admin.email == officer_in.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Official email is already registered.",
            )

        user_id = uuid.uuid4()

        # Provision in Supabase Auth via Admin API if available
        if supabase_admin:
            try:
                auth_res = supabase_admin.auth.admin.create_user({
                    "email": officer_in.email,
                    "password": officer_in.password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": officer_in.full_name,
                        "role": officer_in.role,
                        "user_type": "admin",
                        "department_id": str(officer_in.department_id) if officer_in.department_id else None,
                    },
                })
                if auth_res and auth_res.user:
                    user_id = uuid.UUID(auth_res.user.id)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Supabase Admin provisioning error: {str(e)}",
                )

        # Create Admin database record
        admin = Admin(
            id=user_id,
            department_id=officer_in.department_id,
            role=officer_in.role,
            full_name=officer_in.full_name,
            email=officer_in.email,
            phone=officer_in.phone,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        return AdminProfileResponse.model_validate(admin)

    @staticmethod
    def list_officers(
        db: Session,
        department_id: Optional[UUID] = None,
    ) -> List[AdminProfileResponse]:
        query = db.query(Admin)
        if department_id:
            query = query.filter(Admin.department_id == department_id)
        admins = query.all()
        return [AdminProfileResponse.model_validate(a) for a in admins]
