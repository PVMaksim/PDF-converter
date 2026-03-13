"""
Conversions API endpoints.
Create and track conversion jobs.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.user import User, UserPlan
from ...models.conversion_job import ConversionJob, JobStatus
from ...models.file_record import FileRecord
from ...tasks.convert_task import run_conversion
from ...services.converter import get_converter, ConversionError
from ...middleware.rate_limiter import limiter, get_limit_for_plan
from ...schemas import ConversionCreate, ConversionResponse, JobStatusResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user_with_plan(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Get current user — required for conversion endpoints."""
    from .auth import get_current_user
    return await get_current_user(token=token, db=db)

router = APIRouter(prefix="/conversions", tags=["conversions"])

# Поддерживаемые форматы
SUPPORTED_FORMATS = {"docx", "xlsx", "pptx", "rtf", "html", "png", "jpeg", "jpg", "txt"}


@router.post("/", response_model=ConversionResponse)
@limiter.limit(get_limit_for_plan)
async def create_conversion(
    request: Request,
    body: ConversionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_plan),
):
    """
    Create a new conversion job.
    
    Args:
        body: Conversion request (file_id, target_format)
        db: Database session
        current_user: Authenticated user with plan info
    
    Returns:
        job_id: UUID of created job
        status: Initial job status (pending)
        target_format: Target format
    
    Raises:
        HTTPException: 422 if format not supported, 404 if file not found
    """
    fmt = body.target_format.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported format '{fmt}'. Supported: {sorted(SUPPORTED_FORMATS)}",
        )

    # Проверяем существование файла
    source: FileRecord = await db.get(FileRecord, body.file_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source file not found")

    # Создаём задачу конвертации
    job = ConversionJob(
        user_id=current_user.id,
        target_format=fmt,
        source_file_id=source.id,
        status=JobStatus.PENDING,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Запускаем Celery задачу
    run_conversion.delay(str(job.id))

    return ConversionResponse(
        job_id=str(job.id),
        status=job.status.value,
        target_format=job.target_format,
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_with_plan),
):
    """
    Get conversion job status.
    
    Args:
        job_id: UUID of conversion job
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Job status details
    
    Raises:
        HTTPException: 404 if job not found
    """
    job: ConversionJob = await db.get(ConversionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Проверяем, что пользователь владеет задачей
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return JobStatusResponse(
        job_id=str(job.id),
        status=job.status.value,
        result_file_id=str(job.result_file_id) if job.result_file_id else None,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )
