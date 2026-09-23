from fastapi import FastAPI

# Import routers
from routers.stt_router import router as stt_router
from routers.translation_router import router as translation_router
from routers.duplicate_router import router as duplicate_router
from routers.priority_router import router as priority_router

app = FastAPI(
    title="AI Service API",
    description="FastAPI wrapper for speech‑to‑text, translation, duplicate detection, and priority prediction.",
    version="0.1.0",
)

# Include routers – each router already has the "/ai" prefix
app.include_router(stt_router)
app.include_router(translation_router)
app.include_router(duplicate_router)
app.include_router(priority_router)

# Simple health‑check endpoint
@app.get("/")
def health_check():
    return {"status": "AI service is running"}
