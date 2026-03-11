"""
Cleanup service for expired files.
Deletes files past their TTL.
"""
import logging
from datetime import datetime

from sqlalchemy import select, delete

from ..database import AsyncSessionLocal
from ..models.file_record import FileRecord
from .storage import storage_service

logger = logging.getLogger(__name__)


async def delete_expired_files() -> int:
    """
    Delete file records and their storage objects where expires_at < now.
    
    Called periodically by Celery beat (every 6 hours by default).
    
    Returns:
        Number of files deleted
    
    Example:
        count = await delete_expired_files()
        logger.info(f"Cleaned up {count} expired files")
    """
    now = datetime.utcnow()
    deleted = 0

    async with AsyncSessionLocal() as session:
        # Находим все просроченные файлы
        result = await session.execute(
            select(FileRecord).where(
                FileRecord.expires_at != None,  # noqa: E711
                FileRecord.expires_at < now,
            )
        )
        expired: list[FileRecord] = result.scalars().all()

        for record in expired:
            try:
                # Удаляем из хранилища
                storage_service.delete(record.storage_path)
            except Exception as exc:
                logger.warning(f"Failed to delete {record.storage_path} from storage: {exc}")

            # Удаляем запись из БД
            await session.delete(record)
            deleted += 1

        await session.commit()

    logger.info(f"Cleanup complete: removed {deleted} expired file records")
    return deleted
