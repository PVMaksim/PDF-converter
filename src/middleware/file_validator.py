"""
File validation middleware.
Validates uploaded files by MIME type and size.
"""
import magic
from fastapi import HTTPException, UploadFile

from ..config import settings

# Разрешённые MIME-типы
ALLOWED_MIME_TYPES = {"application/pdf"}

# Лимиты размеров в байтах
MAX_SIZE_FREE = settings.MAX_FILE_SIZE_FREE_MB * 1024 * 1024
MAX_SIZE_PRO = settings.MAX_FILE_SIZE_PRO_MB * 1024 * 1024


async def validate_upload(file: UploadFile, is_pro: bool = False) -> bytes:
    """
    Validate uploaded file by MIME type and size.
    
    Args:
        file: FastAPI UploadFile object
        is_pro: True for PRO users (higher limits)
    
    Returns:
        File content as bytes if validation passes
    
    Raises:
        HTTPException: 413 if file too large, 415 if wrong MIME type
    
    Example:
        content = await validate_upload(file, is_pro=user.plan == UserPlan.PRO)
    """
    # Читаем содержимое файла
    content = await file.read()

    # Проверка размера
    max_size = MAX_SIZE_PRO if is_pro else MAX_SIZE_FREE
    if len(content) > max_size:
        limit_mb = settings.MAX_FILE_SIZE_PRO_MB if is_pro else settings.MAX_FILE_SIZE_FREE_MB
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {limit_mb} MB.",
        )

    # Проверка MIME-типа через libmagic (не только по расширению)
    mime = magic.from_buffer(content, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {mime}. Only PDF files are accepted.",
        )

    return content
