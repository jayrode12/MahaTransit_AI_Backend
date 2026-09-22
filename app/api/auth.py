from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, AuthResponse, MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login for Citizens and Officials",
)
def login(
    login_in: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticates user credentials via Supabase Auth and returns active profile details.
    """
    return AuthService.login(db=db, login_in=login_in)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Sign out user session",
)
def logout():
    """
    Signs out the user session from Supabase Auth.
    """
    return AuthService.logout()
