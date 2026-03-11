"""
Files API endpoints.
Upload and download files with rate limiting.
"""
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import settings
from ...database import get_db
from ...models.user import User, UserPlan
from ...models.file_record import FileRecord
from ...middleware.file_validator import validate_upload
from ...middleware.rate_limiter import limiter, get_limit_for_plan
from ...services.storage import storage_service
from ...schemas import FileUploadResponse, FileDownloadResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileUploadResponse)
@limiter.limit(get_limit_for_plan)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Upload a PDF file for conversion.
    
    Args:
        file: PDF file to upload
        db: Database session
        current_user: Authenticated user (or None for anonymous)
    
    Returns:
        file_id: UUID of uploaded file record
        filename: Original filename
        size_bytes: File size in bytes
    
    Raises:
        HTTPException: 413 if file too large, 415 if not PDF
    """
    # Определяем план пользователя
    is_pro = current_user and current_user.plan == UserPlan.PRO
    
    # Валидируем и читаем файл
    content = await validate_upload(file, is_pro=is_pro)

    # Сохраняем во временный файл для вычисления хэша
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp_path.write_bytes(content)

    # Вычисляем SHA-256 для дедупликации
    sha = storage_service.sha256(tmp_path)

    # Проверяем дедупликацию
    result = await db.execute(select(FileRecord).where(FileRecord.sha256_hash == sha))
    existing = result.scalar_one_or_none()
    if existing:
        tmp_path.unlink(missing_ok=True)
        return {
            "file_id": str(existing.id),
            "filename": existing.original_name,
            "size_bytes": existing.size_bytes,
            "duplicate": True,
        }

    # Определяем TTL на основе плана
    ttl_hours = settings.FILE_TTL_PRO_DAYS * 24 if is_pro else settings.FILE_TTL_FREE_HOURS
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

    # Загружаем в хранилище
    object_key = f"uploads/{sha}/{file.filename}"
    storage_service.upload(tmp_path, object_key)
    tmp_path.unlink(missing_ok=True)

    # Создаём запись в БД
    record = FileRecord(
        storage_path=object_key,
        original_name=file.filename,
        mime_type="application/pdf",
        size_bytes=len(content),
        sha256_hash=sha,
        expires_at=expires_at,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return {
        "file_id": str(record.id),
        "filename": file.filename,
        "size_bytes": len(content),
        "duplicate": False,
    }


@router.get("/download/{file_id}")
async def download_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_optional),
):
    """
    Get a presigned download URL for a file.
    
    Args:
        file_id: UUID of file record
        db: Database session
        current_user: Authenticated user
    
    Returns:
        download_url: Presigned URL (expires in 1 hour)
        filename: Original filename
        expires_in: URL expiration time in seconds
    
    Raises:
        HTTPException: 404 if not found, 410 if expired
    """
    record: FileRecord = await db.get(FileRecord, file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    # Проверяем, не истёк ли файл
    if record.expires_at and record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="File has expired")

    # Генерируем presigned URL
    url = storage_service.get_presigned_url(record.storage_path, expires_in=3600)
    return {
        "download_url": url,
        "filename": record.original_name,
        "expires_in": 3600,
    }


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    For endpoints that work for both authenticated and anonymous users.
    """
    if not token:
        return None

    from .auth import get_current_user
    try:
        return await get_current_user(token=token, db=db)
    except HTTPException:
        return None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
