import magic
from fastapi import HTTPException, UploadFile

from ..config import settings

ALLOWED_MIME_TYPES = {"application/pdf"}
MAX_SIZE_FREE = settings.MAX_FILE_SIZE_FREE_MB * 1024 * 1024
MAX_SIZE_PRO = settings.MAX_FILE_SIZE_PRO_MB * 1024 * 1024


async def validate_upload(file: UploadFile, is_pro: bool = False) -> bytes:
    """
    Read the uploaded file, validate MIME type and size.
    Returns raw bytes on success, raises HTTPException on failure.
    """
    content = await file.read()

    # Check size
    max_size = MAX_SIZE_PRO if is_pro else MAX_SIZE_FREE
    if len(content) > max_size:
        limit_mb = settings.MAX_FILE_SIZE_PRO_MB if is_pro else settings.MAX_FILE_SIZE_FREE_MB
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {limit_mb} MB.",
        )

    # Check MIME type via libmagic (not just extension)
    mime = magic.from_buffer(content, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {mime}. Only PDF files are accepted.",
        )

    return content
