"""
Celery tasks for PDF conversion.
Handles async conversion jobs.
"""
import asyncio
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from celery import Task

from .celery_app import celery_app
from ..config import settings
from ..database import AsyncSessionLocal
from ..models.conversion_job import ConversionJob, JobStatus
from ..models.file_record import FileRecord
from ..models.user import UserPlan
from ..services.converter import get_converter, ConversionError
from ..services.storage import storage_service
from ..utils.error_notifier import notify_admin

logger = logging.getLogger(__name__)


def _run_async(coro):
    """
    Run an async coroutine from a sync Celery task.
    
    Note: This creates a new event loop. For better async handling,
    consider using celery[redis] with async support.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    name="src.tasks.convert_task.run_conversion",
)
def run_conversion(self, job_id: str):
    """
    Main conversion task.
    
    Steps:
    1. Load ConversionJob from DB
    2. Download source PDF from storage
    3. Convert to target format
    4. Upload result to storage
    5. Update job status (done/failed)
    
    Args:
        job_id: UUID of conversion job
    """
    return _run_async(_async_run_conversion(job_id, self))


async def _async_run_conversion(job_id: str, task):
    """Async implementation of conversion task."""
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
            # 1. Скачиваем исходный файл
            async with AsyncSessionLocal() as session:
                job = await session.get(ConversionJob, UUID(job_id))
                source_record: FileRecord = await session.get(FileRecord, job.source_file_id)

            storage_service.download(source_record.storage_path, source_pdf)

            # 2. Конвертируем
            converter = get_converter(job.target_format)
            result_path = await converter.convert(source_pdf, output_path)

            # 3. Загружаем результат в хранилище
            object_key = f"results/{job_id}/{result_path.name}"
            storage_service.upload(result_path, object_key)

            # 4. Определяем TTL на основе плана пользователя
            async with AsyncSessionLocal() as session:
                job = await session.get(ConversionJob, UUID(job_id))
                user = await session.get(User, job.user_id)
                plan = getattr(user, "plan", UserPlan.FREE) if user else UserPlan.FREE
                
                if plan == UserPlan.FREE:
                    expires_at = datetime.utcnow() + timedelta(hours=settings.FILE_TTL_FREE_HOURS)
                else:
                    expires_at = datetime.utcnow() + timedelta(days=settings.FILE_TTL_PRO_DAYS)

                # Создаём запись результирующего файла
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

                # Обновляем задачу
                job.result_file_id = result_record.id
                job.status = JobStatus.DONE
                job.completed_at = datetime.utcnow()
                job.expires_at = expires_at
                await session.commit()

            logger.info(f"Job {job_id} completed → {result_path.name}")

        except Exception as exc:
            logger.error(f"Job {job_id} failed: {exc}", exc_info=True)
            
            # Уведомляем админа об ошибке
            await notify_admin(
                exc,
                context=f"Conversion job {job_id} failed",
            )
            
            async with AsyncSessionLocal() as session:
                job = await session.get(ConversionJob, UUID(job_id))
                if job:
                    job.status = JobStatus.FAILED
                    job.error_message = str(exc)
                    job.completed_at = datetime.utcnow()
                    await session.commit()

            # Повторяем задачу
            try:
                raise task.retry(exc=exc)
            except Exception:
                pass


@celery_app.task(name="src.tasks.convert_task.cleanup_expired_files_task")
def cleanup_expired_files_task():
    """
    Periodic task to delete expired files.
    Called by Celery beat every 6 hours.
    """
    from ..services.cleanup import delete_expired_files
    count = _run_async(delete_expired_files())
    logger.info(f"Cleanup task finished: {count} files removed")


@celery_app.task(name="src.tasks.convert_task.aggregate_stats_task")
def aggregate_stats_task():
    """
    Periodic task to aggregate conversion statistics.
    Called daily by Celery beat.
    """
    # TODO: Aggregate daily conversion statistics into DB
    logger.info("Stats aggregation task (not yet implemented)")


def _mime_for(fmt: str) -> str:
    """
    Get MIME type for file format.
    
    Args:
        fmt: File format extension (docx, png, etc.)
    
    Returns:
        MIME type string
    """
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


# Import User model for type hints
from ..models.user import User
