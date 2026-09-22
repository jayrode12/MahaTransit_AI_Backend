import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.citizen import Citizen
from app.schemas.citizen import CitizenRegister, CitizenProfileResponse, CitizenProfileUpdate
from app.core.supabase import supabase_client, supabase_admin


class CitizenService:
    """
    Business service managing Citizen registration and profile lifecycle.
    """

    @staticmethod
    def register(db: Session, reg_in: CitizenRegister) -> CitizenProfileResponse:
        # Check email uniqueness
        if db.query(Citizen).filter(Citizen.email == reg_in.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered.",
            )

        user_id = uuid.uuid4()

        # Register in Supabase Auth
        if supabase_admin:
            try:
                auth_res = supabase_admin.auth.admin.create_user({
                    "email": reg_in.email,
                    "password": reg_in.password,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": reg_in.full_name,
                        "user_type": "citizen",
                    },
                })
                if auth_res and auth_res.user:
                    user_id = uuid.UUID(auth_res.user.id)
            except Exception as e:
                # Fallback to standard sign_up if admin API is restricted
                if supabase_client:
                    try:
                        auth_res = supabase_client.auth.sign_up({
                            "email": reg_in.email,
                            "password": reg_in.password,
                            "options": {
                                "data": {
                                    "full_name": reg_in.full_name,
                                    "user_type": "citizen",
                                }
                            }
                        })
                        if auth_res and auth_res.user:
                            user_id = uuid.UUID(auth_res.user.id)
                    except Exception as client_err:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Supabase Auth error: {str(client_err)}",
                        )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Supabase Auth error: {str(e)}",
                    )
        elif supabase_client:
            try:
                auth_res = supabase_client.auth.sign_up({
                    "email": reg_in.email,
                    "password": reg_in.password,
                    "options": {
                        "data": {
                            "full_name": reg_in.full_name,
                            "user_type": "citizen",
                        }
                    }
                })
                if auth_res and auth_res.user:
                    user_id = uuid.UUID(auth_res.user.id)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Supabase Auth error: {str(e)}",
                )

        # Create Citizen record
        citizen = Citizen(
            id=user_id,
            full_name=reg_in.full_name,
            email=reg_in.email,
            phone=reg_in.phone,
            preferred_language=reg_in.preferred_language or "en",
        )
        db.add(citizen)
        db.commit()
        db.refresh(citizen)

        return CitizenProfileResponse.model_validate(citizen)

    @staticmethod
    def get_profile(citizen: Citizen) -> CitizenProfileResponse:
        return CitizenProfileResponse.model_validate(citizen)

    @staticmethod
    def update_profile(
        db: Session,
        citizen: Citizen,
        update_in: CitizenProfileUpdate,
    ) -> CitizenProfileResponse:
        if update_in.full_name is not None:
            citizen.full_name = update_in.full_name
        if update_in.phone is not None:
            citizen.phone = update_in.phone
        if update_in.preferred_language is not None:
            citizen.preferred_language = update_in.preferred_language

        db.commit()
        db.refresh(citizen)
        return CitizenProfileResponse.model_validate(citizen)
