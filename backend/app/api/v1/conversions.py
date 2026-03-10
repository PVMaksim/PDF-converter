from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models import ConversionJob, JobStatus, User, UserPlan, FileRecord
from ...tasks.convert_task import run_conversion
from ...services.converter import GOTENBERG_FORMATS, PYMUPDF_FORMATS

router = APIRouter(prefix="/conversions", tags=["conversions"])

SUPPORTED_FORMATS = GOTENBERG_FORMATS | PYMUPDF_FORMATS


class ConversionRequest(BaseModel):
    file_id: UUID
    target_format: str


class ConversionResponse(BaseModel):
    job_id: str
    status: str
    target_format: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result_file_id: str | None = None
    error_message: str | None = None
    created_at: str
    completed_at: str | None = None


@router.post("/", response_model=ConversionResponse)
async def create_conversion(
    body: ConversionRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: inject current_user
):
    fmt = body.target_format.lower()
    if fmt not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported format '{fmt}'. Supported: {sorted(SUPPORTED_FORMATS)}",
        )

    source: FileRecord = await db.get(FileRecord, body.file_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source file not found")

    # TODO: enforce daily_limit from user plan

    # Placeholder user — replace with current_user injection
    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    job = ConversionJob(
        user_id=user.id,
        target_format=fmt,
        source_file_id=source.id,
        status=JobStatus.PENDING,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch Celery task
    run_conversion.delay(str(job.id))

    return ConversionResponse(
        job_id=str(job.id),
        status=job.status.value,
        target_format=job.target_format,
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: UUID, db: AsyncSession = Depends(get_db)):
    job: ConversionJob = await db.get(ConversionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=str(job.id),
        status=job.status.value,
        result_file_id=str(job.result_file_id) if job.result_file_id else None,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )
