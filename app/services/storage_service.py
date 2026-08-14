import mimetypes
import re
import uuid
from typing import Optional, Tuple
from uuid import UUID

from supabase import create_client, Client

from app.core.config import settings


class StorageService:
    """
    Service for managing file uploads to Supabase Storage:
    - Audio voice notes -> 'voice-files' bucket
    - Documents, images, and other attachments -> 'attachments' bucket
    """

    _client: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """
        Lazily initializes and returns the Supabase storage client.
        """
        if cls._client is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise RuntimeError(
                    "SUPABASE_URL and SUPABASE_KEY must be configured in .env to use Supabase Storage."
                )
            cls._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return cls._client

    @classmethod
    def determine_attachment_type(cls, file_name: str, mime_type: Optional[str] = None) -> str:
        """
        Detects attachment type: 'audio', 'image', 'video', or 'document'.
        """
        inferred_mime, _ = mimetypes.guess_type(file_name)
        effective_mime = mime_type or inferred_mime or ""

        if effective_mime.startswith("audio/") or file_name.lower().endswith(
            (".mp3", ".wav", ".m4a", ".ogg", ".webm", ".aac", ".flac")
        ):
            return "audio"
        elif effective_mime.startswith("image/") or file_name.lower().endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg")
        ):
            return "image"
        elif effective_mime.startswith("video/") or file_name.lower().endswith(
            (".mp4", ".mov", ".avi", ".mkv", ".webm")
        ):
            return "video"
        else:
            return "document"

    @classmethod
    def get_destination_bucket(cls, attachment_type: str) -> str:
        """
        Routes audio voice files to 'voice-files' bucket and others to 'attachments' bucket.
        """
        if attachment_type == "audio":
            return settings.SUPABASE_VOICE_BUCKET or "voice-files"
        return settings.SUPABASE_ATTACHMENTS_BUCKET or "attachments"

    @classmethod
    def upload_file(
        cls,
        file_bytes: bytes,
        file_name: str,
        mime_type: Optional[str] = None,
        complaint_id: Optional[UUID] = None,
        forced_attachment_type: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """
        Uploads file to the appropriate Supabase bucket and returns (public_url, attachment_type, storage_path).
        """
        client = cls.get_client()

        # Determine attachment type & destination bucket
        attachment_type = (
            forced_attachment_type
            if forced_attachment_type
            else cls.determine_attachment_type(file_name, mime_type)
        )
        bucket_name = cls.get_destination_bucket(attachment_type)

        # Sanitize filename & create unique storage path
        clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", file_name)
        folder = f"complaints/{complaint_id}" if complaint_id else "complaints/general"
        file_path = f"{folder}/{uuid.uuid4()}_{clean_name}"

        # Resolve MIME type
        inferred_mime, _ = mimetypes.guess_type(file_name)
        content_type = mime_type or inferred_mime or "application/octet-stream"

        # Upload to Supabase Storage
        file_options = {"content-type": content_type}
        client.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_bytes,
            file_options=file_options,
        )

        # Get public URL
        public_url = client.storage.from_(bucket_name).get_public_url(file_path)

        return public_url, attachment_type, file_path
