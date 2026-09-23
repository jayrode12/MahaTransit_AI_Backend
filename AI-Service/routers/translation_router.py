from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

# Import the translation function
from translation.translator import translate_to_english

router = APIRouter(prefix="/ai", tags=["Translation"])

class TranslateRequest(BaseModel):
    text: str
    source: str

class TranslateResponse(BaseModel):
    translatedText: str

@router.post("/translate", response_model=TranslateResponse)
def translate(request: TranslateRequest):
    """Translate the provided text to English.
    The source language code should be one of the supported codes (e.g., "hi").
    """
    try:
        translated = translate_to_english(request.text, request.source)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return TranslateResponse(translatedText=translated)
