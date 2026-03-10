from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging
from datetime import datetime, timedelta

from ..database import get_db
from ..models.conversion_job import ConversionJob, JobStatus
from ..services.file_storage import FileStorage

logger = logging.getLogger(__name__)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /stats command - show conversion statistics
    """
    async with get_db() as db:
        # Total jobs
        total_result = await db.execute(
            select(func.count()).select_from(ConversionJob)
        )
        total = total_result.scalar() or 0

        # Jobs by status
        status_counts = {}
        for status in JobStatus:
            count_result = await db.execute(
                select(func.count()).select_from(ConversionJob).where(
                    ConversionJob.status == status
                )
            )
            status_counts[status.value] = count_result.scalar() or 0

        # Recent jobs (last 24h)
        day_ago = datetime.utcnow() - timedelta(days=1)
        recent_result = await db.execute(
            select(func.count()).select_from(ConversionJob).where(
                ConversionJob.created_at >= day_ago
            )
        )
        recent = recent_result.scalar() or 0

    stats_message = f"""
📊 Статистика конвертаций:

Всего заданий: {total}
├─ ✅ Завершено: {status_counts.get('completed', 0)}
├─ ⏳ В процессе: {status_counts.get('processing', 0)}
├─ ❌ Ошибки: {status_counts.get('failed', 0)}
└─ ⏸️ Ожидание: {status_counts.get('pending', 0)}

За последние 24 часа: {recent}
"""
    await update.message.reply_text(stats_message)


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /broadcast command - send message to all users
    Admin only - to be implemented with proper auth
    """
    # TODO: Implement admin authentication
    await update.message.reply_text(
        "⚠️ Эта команда требует прав администратора и пока не реализована."
    )


async def cleanup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /cleanup command - manually trigger file cleanup
    """
    storage = FileStorage()
    cleaned = storage.cleanup_old_files()

    await update.message.reply_text(
        f"🧹 Очистка завершена.\nУдалено старых файлов: {cleaned}"
    )