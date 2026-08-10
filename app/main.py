from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.complaints import router as complaints_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent Public Transport Complaint Management System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware Configuration (for React frontend)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register API v1 Routers
app.include_router(complaints_router, prefix=settings.API_V1_STR)
