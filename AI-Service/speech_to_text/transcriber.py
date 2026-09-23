import os
from typing import Dict

# Import the actual Whisper library. It must be installed (pip install openai-whisper).
# If the import fails, the error will propagate, making the endpoint unusable until the
# dependency is resolved – this is intentional to avoid silent dummy behavior.
import whisper  # type: ignore

# Singleton model instance – loaded lazily on the first call.
_model_instance = None

def _load_model(model_size: str = "small"):
    """Load the Whisper model once and cache it.
    The *model_size* argument is kept for API compatibility; you can choose any
    size supported by Whisper (e.g., "tiny", "base", "small", "medium", "large").
    """
    global _model_instance
    if _model_instance is None:
        print(f"Loading Whisper '{model_size}' model... (only happens once)")
        _model_instance = whisper.load_model(model_size)
    return _model_instance

def transcribe_audio(file_path: str, model_size: str = "small") -> Dict[str, str]:
    """Transcribe an audio file and return a dict with ``text`` and ``language``.
    This uses the real Whisper model now that the dependency is present.
    """
    model = _load_model(model_size)
    result = model.transcribe(file_path)
    # Ensure the expected keys are present.
    return {"text": result.get("text", "").strip(), "language": result.get("language", "en")}
