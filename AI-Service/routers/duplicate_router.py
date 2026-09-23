from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# Import duplicate detection utilities
from duplicate_detection.duplicate_checker import check_duplicate
from duplicate_detection.similarity import load_model as load_similarity_model
from datasets.sample_complaints import SAMPLE_COMPLAINTS

router = APIRouter(prefix="/ai", tags=["Duplicate Detection"])

class DuplicateRequest(BaseModel):
    text: str
    id: str
    existing_complaints: Optional[List[Dict[str, Any]]] = None

class DuplicateResponse(BaseModel):
    isDuplicate: bool
    duplicateOf: Optional[str]
    score: Optional[float]
    assigned_group_id: Optional[str] = None

# Cache the similarity model to avoid reloading on each request
_similarity_model = None

def get_similarity_model():
    global _similarity_model
    if _similarity_model is None:
        _similarity_model = load_similarity_model()
    return _similarity_model

def prepare_complaints(complist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Add embeddings to a list of complaint dicts.
    Expected keys in each dict: 'id' and 'text'. The function returns a new list
    where each dict also contains an 'embedding' entry (tensor) and an optional
    'duplicate_group_id' (initially None).
    """
    model = get_similarity_model()
    prepared = []
    for comp in complist:
        embedding = model.encode(comp["text"], convert_to_tensor=True)
        prepared.append({
            "id": comp["id"],
            "text": comp["text"],
            "embedding": embedding,
            "duplicate_group_id": None,
        })
    return prepared

@router.post("/detect-duplicate", response_model=DuplicateResponse)
def detect_duplicate(request: DuplicateRequest):
    """Detect whether *request.text* is a duplicate of an existing complaint.
    If *existing_complaints* is provided, it is used; otherwise the temporary
    SAMPLE_COMPLAINTS list is used as a placeholder until a real database is
    integrated (Phase 6).
    """
    # Choose source of existing complaints
    source = request.existing_complaints if request.existing_complaints is not None else SAMPLE_COMPLAINTS
    # Ensure each complaint has an embedding and group id field
    complaints_with_embeddings = prepare_complaints(source)
    try:
        result = check_duplicate(request.text, request.id, complaints_with_embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return DuplicateResponse(**result)
