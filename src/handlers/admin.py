"""
Telegram bot admin handlers.
Stats and cleanup commands for administrators.
"""
import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select, func

from ..database import AsyncSessionLocal
from ..models.conversion_job import ConversionJob, JobStatus
from ..services.cleanup import delete_expired_files

logger = logging.getLogger(__name__)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /stats command.
    Show conversion statistics (admin only).
    """
    async with AsyncSessionLocal() as session:
        # Общее количество задач
        result = await session.execute(select(func.count()).select_from(ConversionJob))
        total = result.scalar() or 0

        # Количество по статусам
        status_counts = {}
        for status in JobStatus:
            result = await session.execute(
                select(func.count()).select_from(ConversionJob).where(
                    ConversionJob.status == status
                )
            )
            status_counts[status.value] = result.scalar() or 0

        # За последние 24 часа
        day_ago = datetime.utcnow() - timedelta(days=1)
        result = await session.execute(
            select(func.count()).select_from(ConversionJob).where(
                ConversionJob.created_at >= day_ago
            )
        )
        recent = result.scalar() or 0

    stats_message = f"""
📊 Статистика конвертаций:

Всего заданий: {total}
├─ ✅ Завершено: {status_counts.get('done', 0)}
├─ ⏳ В процессе: {status_counts.get('processing', 0)}
├─ ❌ Ошибки: {status_counts.get('failed', 0)}
└─ ⏸️ Ожидание: {status_counts.get('pending', 0)}

За последние 24 часа: {recent}
"""
    await update.message.reply_text(stats_message)


async def cleanup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /cleanup command.
    Manually trigger expired files cleanup.
    """
    await update.message.reply_text("🧹 Запускаю очистку старых файлов...")
    
    try:
        count = await delete_expired_files()
        await update.message.reply_text(f"✅ Очистка завершена.\nУдалено файлов: {count}")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка при очистке: {str(e)}")
