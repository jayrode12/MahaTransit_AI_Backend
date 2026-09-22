from app.api.auth import router as auth_router
from app.api.citizens import router as citizens_router
from app.api.admins import router as admins_router
from app.api.complaints import router as complaints_router

__all__ = [
    "auth_router",
    "citizens_router",
    "admins_router",
    "complaints_router",
]
