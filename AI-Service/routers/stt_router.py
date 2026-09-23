from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from pathlib import Path

# Import the transcription function
from speech_to_text.transcriber import transcribe_audio

router = APIRouter(prefix="/ai", tags=["Speech to Text"])

@router.post("/speech-to-text")
async def speech_to_text(voiceFile: UploadFile = File(...)):
    """Accept an audio file, run transcription, and return text + language.
    The uploaded file is saved to a temporary location, processed, then
    deleted to avoid disk buildup.
    """
    # Create a temporary file path in the system's temp directory
    temp_dir = Path(os.getenv("TMP", "/tmp"))
    temp_path = temp_dir / f"tmp_{voiceFile.filename}"
    try:
        # Write uploaded content to temp file
        with open(temp_path, "wb") as out_file:
            content = await voiceFile.read()
            out_file.write(content)
        # Run the transcription function (assumed to return (text, language))
        result = transcribe_audio(str(temp_path))
        if not isinstance(result, (list, tuple)) or len(result) != 2:
            raise HTTPException(status_code=500, detail="Invalid transcribe_audio return value")
        text, language = result
        return {"text": text, "language": language}
    finally:
        # Ensure the temporary file is removed even if an error occurs
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
