from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
import os
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer

# Paths to saved artefacts (relative to project root)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "priority_model.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "priority_encoder.pkl")
LABEL_ENCODER_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "priority_label_encoder.pkl")

router = APIRouter(prefix="/ai", tags=["Priority Prediction"])

class PriorityRequest(BaseModel):
    text: str
    transport_type: Literal["Metro", "Bus", "Local Train"]
    location: Literal["Andheri", "Dadar", "Borivali", "Kurla", "Virar", "Churchgate", "Ghatkopar", "Thane"]
    duplicate_score: float
    previous_complaints: int
    severity_indicator: Literal["safety", "comfort", "cleanliness", "delay", "staff_behavior"]

class PriorityResponse(BaseModel):
    priority: str
    confidence: float

# Lazy‑load artefacts only once per process
_model = None
_encoder = None
_label_encoder = None
_text_encoder = None

def load_artefacts():
    global _model, _encoder, _label_encoder, _text_encoder
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    if _encoder is None:
        _encoder = joblib.load(ENCODER_PATH)
    if _label_encoder is None:
        _label_encoder = joblib.load(LABEL_ENCODER_PATH)
    if _text_encoder is None:
        _text_encoder = SentenceTransformer("all-MiniLM-L6-v2")

@router.post("/predict-priority", response_model=PriorityResponse)
def predict_priority(req: PriorityRequest):
    """Predict priority for a complaint.
    Returns the predicted priority label and the model confidence (probability of the predicted class).
    """
    try:
        load_artefacts()
        # 1. Text embedding
        text_emb = _text_encoder.encode([req.text], show_progress_bar=False)
        # 2. One‑hot encode categorical columns (transport_type, location, severity_indicator)
        cat_array = _encoder.transform([[req.transport_type, req.location, req.severity_indicator]])
        # 3. Numeric features
        numeric = np.array([[req.duplicate_score, req.previous_complaints]])
        # 4. Build feature vector
        X = np.hstack([text_emb, cat_array, numeric])
        # 5. Predict class probabilities
        probs = _model.predict_proba(X)[0]
        pred_idx = int(np.argmax(probs))
        priority_label = _label_encoder.inverse_transform([pred_idx])[0]
        confidence = float(probs[pred_idx])
        return PriorityResponse(priority=priority_label, confidence=round(confidence, 4))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
