from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.citizen import Citizen
from app.schemas.citizen import CitizenRegister, CitizenProfileResponse, CitizenProfileUpdate
from app.services.citizen_service import CitizenService
from app.api.deps import get_current_citizen

router = APIRouter(prefix="/citizens", tags=["Citizens"])


@router.post(
    "/register",
    response_model=CitizenProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new citizen",
)
def register_citizen(
    reg_in: CitizenRegister,
    db: Session = Depends(get_db),
):
    """
    Registers a new citizen via Supabase Auth and creates a profile in the citizens database.
    """
    return CitizenService.register(db=db, reg_in=reg_in)


@router.get(
    "/profile",
    response_model=CitizenProfileResponse,
    summary="Get current citizen profile",
)
def get_citizen_profile(
    current_citizen: Citizen = Depends(get_current_citizen),
):
    """
    Fetches profile for the currently authenticated citizen.
    """
    return CitizenService.get_profile(citizen=current_citizen)


@router.put(
    "/profile",
    response_model=CitizenProfileResponse,
    summary="Update citizen profile",
)
def update_citizen_profile(
    update_in: CitizenProfileUpdate,
    current_citizen: Citizen = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """
    Updates profile attributes (name, phone, language) for the authenticated citizen.
    """
    return CitizenService.update_profile(
        db=db,
        citizen=current_citizen,
        update_in=update_in,
    )
