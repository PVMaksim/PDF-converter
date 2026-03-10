import asyncio
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from .celery_app import celery_app
from ..config import settings
from ..database import AsyncSessionLocal
from ..models import ConversionJob, FileRecord, JobStatus, UserPlan
from ..services.converter import get_converter, ConversionError
from ..services.storage import storage_service

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    name="app.tasks.convert_task.run_conversion",
)
def run_conversion(self, job_id: str):
    """
    Main conversion task.
    1. Load ConversionJob from DB
    2. Download source PDF from MinIO
    3. Convert to target format
    4. Upload result to MinIO
    5. Update job status → done / failed
    """
    return _run_async(_async_run_conversion(job_id, self))


async def _async_run_conversion(job_id: str, task):
    async with AsyncSessionLocal() as session:
        job: ConversionJob = await session.get(ConversionJob, UUID(job_id))
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        job.status = JobStatus.PROCESSING
        await session.commit()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        source_pdf = tmp_path / "input.pdf"
        output_path = tmp_path / f"output.{job.target_format}"

        try:
            # 1. Download source
            async with AsyncSessionLocal() as session:
                job = await session.get(ConversionJob, UUID(job_id))
                source_record: FileRecord = await session.get(FileRecord, job.source_file_id)

            storage_service.download(source_record.storage_path, source_pdf)

            # 2. Convert
            converter = get_converter(job.target_format)
            result_path = await converter.convert(source_pdf, output_path)

            # 3. Upload result
            object_key = f"results/{job_id}/{result_path.name}"
            storage_service.upload(result_path, object_key)

            # 4. Determine TTL based on user plan
            async with AsyncSessionLocal() as session:
                job = await session.get(ConversionJob, UUID(job_id))
                user = await session.get(job.__class__, job.user_id)  # type: ignore
                plan = getattr(user, "plan", UserPlan.FREE) if user else UserPlan.FREE
                if plan == UserPlan.FREE:
                    expires_at = datetime.utcnow() + timedelta(hours=settings.FILE_TTL_FREE_HOURS)
                else:
                    expires_at = datetime.utcnow() + timedelta(days=settings.FILE_TTL_PRO_DAYS)

                result_record = FileRecord(
                    storage_path=object_key,
                    original_name=result_path.name,
                    mime_type=_mime_for(job.target_format),
                    size_bytes=result_path.stat().st_size,
                    sha256_hash=storage_service.sha256(result_path),
                    expires_at=expires_at,
                )
                session.add(result_record)
                await session.flush()

                job.result_file_id = result_record.id
                job.status = JobStatus.DONE
                job.completed_at = datetime.utcnow()
                job.expires_at = expires_at
                await session.commit()

            logger.info(f"Job {job_id} completed → {result_path.name}")

        except Exception as exc:
            logger.error(f"Job {job_id} failed: {exc}", exc_info=True)
            async with AsyncSessionLocal() as session:
                job = await session.get(ConversionJob, UUID(job_id))
                if job:
                    job.status = JobStatus.FAILED
                    job.error_message = str(exc)
                    job.completed_at = datetime.utcnow()
                    await session.commit()

            try:
                raise task.retry(exc=exc)
            except Exception:
                pass


@celery_app.task(name="app.tasks.convert_task.cleanup_expired_files_task")
def cleanup_expired_files_task():
    from ..services.cleanup import delete_expired_files
    count = _run_async(delete_expired_files())
    logger.info(f"Cleanup task finished: {count} files removed")


@celery_app.task(name="app.tasks.convert_task.aggregate_stats_task")
def aggregate_stats_task():
    # TODO: aggregate daily conversion statistics into DB
    logger.info("Stats aggregation task (not yet implemented)")


def _mime_for(fmt: str) -> str:
    return {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "pdf": "application/pdf",
        "txt": "text/plain",
        "rtf": "application/rtf",
        "html": "text/html",
        "png": "image/png",
        "jpeg": "image/jpeg",
        "zip": "application/zip",
    }.get(fmt.lower(), "application/octet-stream")
