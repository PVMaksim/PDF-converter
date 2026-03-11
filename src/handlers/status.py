"""
Telegram bot status handler.
Check conversion job status by ID.
"""
import logging
from uuid import UUID

from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..models.conversion_job import ConversionJob, JobStatus

logger = logging.getLogger(__name__)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /status command.
    Shows conversion job progress.
    
    Usage: /status <job_id>
    Example: /status 550e8400-e29b-41d4-a716-446655440000
    """
    args = context.args
    if not args:
        await update.message.reply_text(
            "ℹ️ Usage: /status <job_id>\n"
            "Пример: /status 550e8400-e29b-41d4-a716-446655440000"
        )
        return

    raw_id = args[0].strip()
    try:
        job_id = UUID(raw_id)
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID задачи.")
        return

    async with AsyncSessionLocal() as session:
        job = await session.get(ConversionJob, job_id)

    if not job:
        await update.message.reply_text("❌ Задача не найдена.")
        return

    # Статус с эмодзи
    status_emoji = {
        JobStatus.PENDING: "⏳",
        JobStatus.PROCESSING: "⚙️",
        JobStatus.DONE: "✅",
        JobStatus.FAILED: "❌",
    }.get(job.status, "❓")

    msg_lines = [
        f"{status_emoji} Задача: `{job.id}`",
        f"Статус: *{job.status.value.upper()}*",
        f"Формат: PDF → {job.target_format.upper()}",
        f"Создана: {job.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
    ]

    if job.status == JobStatus.DONE:
        msg_lines.append("\n📥 Файл готов к скачиванию!")
        # Генерируем ссылку на скачивание
        if job.result_file_id:
            from ..services.storage import storage_service
            from ..models.file_record import FileRecord
            
            result = await session.get(FileRecord, job.result_file_id)
            if result:
                try:
                    url = storage_service.get_presigned_url(result.storage_path)
                    msg_lines.append(f"Скачать: {url}")
                except Exception:
                    pass
    elif job.status == JobStatus.FAILED:
        msg_lines.append(f"\nОшибка: {job.error_message}")

    await update.message.reply_text(
        "\n".join(msg_lines),
        parse_mode="Markdown",
    )
