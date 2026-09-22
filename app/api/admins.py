from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.admin import Admin
from app.schemas.admin import AdminProfileResponse, AdminOfficerCreate
from app.services.admin_service import AdminService
from app.api.deps import get_current_admin, require_roles

router = APIRouter(prefix="/admins", tags=["Admins & Officials"])


@router.get(
    "/profile",
    response_model=AdminProfileResponse,
    summary="Get current official profile",
)
def get_admin_profile(
    current_admin: Admin = Depends(get_current_admin),
):
    """
    Fetches profile for the currently authenticated admin or department official.
    """
    return AdminService.get_profile(admin=current_admin)


@router.post(
    "/officers",
    response_model=AdminProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Provision a new Department Officer / Official",
)
def create_officer(
    officer_in: AdminOfficerCreate,
    current_admin: Admin = Depends(require_roles(["super_admin", "department_admin"])),
    db: Session = Depends(get_db),
):
    """
    Provisions a new official in Supabase Auth and registers them in the admins database.
    Requires super_admin or department_admin role.
    """
    return AdminService.create_officer(db=db, officer_in=officer_in)


@router.get(
    "/officers",
    response_model=List[AdminProfileResponse],
    summary="List department officers",
)
def list_officers(
    department_id: Optional[UUID] = Query(None, description="Filter by department UUID"),
    current_admin: Admin = Depends(require_roles(["super_admin", "department_admin"])),
    db: Session = Depends(get_db),
):
    """
    Lists department officers with optional department filter.
    Requires super_admin or department_admin role.
    """
    return AdminService.list_officers(db=db, department_id=department_id)
