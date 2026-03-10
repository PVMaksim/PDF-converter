import logging
from datetime import datetime

from sqlalchemy import select, delete

from ..database import AsyncSessionLocal
from ..models import FileRecord
from .storage import storage_service

logger = logging.getLogger(__name__)


async def delete_expired_files() -> int:
    """
    Delete FileRecord rows and their MinIO objects where expires_at < now.
    Called by Celery beat every 6 hours.
    Returns count of deleted records.
    """
    now = datetime.utcnow()
    deleted = 0

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(FileRecord).where(
                FileRecord.expires_at != None,  # noqa: E711
                FileRecord.expires_at < now,
            )
        )
        expired: list[FileRecord] = result.scalars().all()

        for record in expired:
            try:
                storage_service.delete(record.storage_path)
            except Exception as exc:
                logger.warning(f"Failed to delete {record.storage_path} from MinIO: {exc}")

            await session.delete(record)
            deleted += 1

        await session.commit()

    logger.info(f"Cleanup: removed {deleted} expired file records")
    return deleted
