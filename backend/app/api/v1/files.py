import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import settings
from ...database import get_db
from ...models import FileRecord, User, UserPlan
from ...middleware.file_validator import validate_upload
from ...services.storage import storage_service

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    # TODO: inject current_user when auth is wired up
):
    """Upload a PDF and store it in MinIO. Returns file_id."""
    # Assume free tier for now — swap with current_user.plan
    is_pro = False
    content = await validate_upload(file, is_pro=is_pro)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp_path.write_bytes(content)

    sha = storage_service.sha256(tmp_path)

    # TODO: deduplication — check if sha256 already in DB

    ttl_hours = settings.FILE_TTL_PRO_DAYS * 24 if is_pro else settings.FILE_TTL_FREE_HOURS
    expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

    object_key = f"uploads/{sha}/{file.filename}"
    storage_service.upload(tmp_path, object_key)
    tmp_path.unlink(missing_ok=True)

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

    return {"file_id": str(record.id), "filename": file.filename, "size_bytes": len(content)}


@router.get("/download/{file_id}")
async def download_file(
    file_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a presigned download URL for a result file."""
    record: FileRecord = await db.get(FileRecord, file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    if record.expires_at and record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="File has expired")

    url = storage_service.get_presigned_url(record.storage_path, expires_in=3600)
    return {"download_url": url, "filename": record.original_name, "expires_in": 3600}
