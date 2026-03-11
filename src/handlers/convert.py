"""
Telegram bot convert handler.
Handles PDF file uploads and format selection.
"""
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from telegram import Update
from telegram.ext import ContextTypes, InlineKeyboardButton, InlineKeyboardMarkup

from ..database import AsyncSessionLocal
from ..models.user import User, UserPlan
from sqlalchemy import select
from ..models.file_record import FileRecord
from ..models.conversion_job import ConversionJob, JobStatus
from ..tasks.convert_task import run_conversion
from ..services.storage import storage_service
from ..config import settings

logger = logging.getLogger(__name__)

# Поддерживаемые форматы с эмодзи
FORMATS = [
    [("📄 DOCX", "docx"), ("📊 XLSX", "xlsx")],
    [("📈 PPTX", "pptx"), ("📝 TXT", "txt")],
    [("🖼️ PNG", "png"), ("🖼️ JPEG", "jpeg")],
    [("🌐 HTML", "html"), ("📋 RTF", "rtf")],
]

SUPPORTED_FORMATS = {fmt for row in FORMATS for _, fmt in row}


def get_format_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard with supported output formats."""
    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"format_{data}")]
        for row in FORMATS
        for text, data in row
    ]
    return InlineKeyboardMarkup(keyboard)


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming PDF document.
    Downloads file, stores it, and asks for output format.
    """
    document = update.message.document
    user_tg_id = update.effective_user.id

    # Проверяем, что это PDF
    if not document.file_name or not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте PDF файл.\n"
            "Я поддерживаю только PDF для конвертации."
        )
        return

    # Скачиваем файл
    try:
        file = await document.get_file()
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        await update.message.reply_text("❌ Ошибка при получении файла. Попробуйте еще раз.")
        return

    # Сохраняем во временный файл
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        await file.download_to_drive(tmp_path)

    try:
        # Вычисляем хэш и размер
        sha = storage_service.sha256(tmp_path)
        size = tmp_path.stat().st_size

        # Проверяем лимит размера (для free пользователей)
        max_size = settings.MAX_FILE_SIZE_FREE_MB * 1024 * 1024
        if size > max_size:
            await update.message.reply_text(
                f"❌ Файл слишком большой.\n"
                f"Максимальный размер: {settings.MAX_FILE_SIZE_FREE_MB} МБ"
            )
            return

        # Загружаем в хранилище
        object_key = f"uploads/{sha}/{document.file_name}"
        storage_service.upload(tmp_path, object_key)

        # Создаём запись в БД
        async with AsyncSessionLocal() as session:
            # Находим или создаём пользователя
            result = await session.execute(select(User).where(User.tg_id == user_tg_id))
            user = result.scalar_one_or_none()
            if not user:
                user = User(tg_id=user_tg_id, plan=UserPlan.FREE)
                session.add(user)
                await session.flush()

            # Создаём запись файла
            expires_at = datetime.utcnow() + timedelta(hours=settings.FILE_TTL_FREE_HOURS)
            file_record = FileRecord(
                storage_path=object_key,
                original_name=document.file_name,
                mime_type="application/pdf",
                size_bytes=size,
                sha256_hash=sha,
                expires_at=expires_at,
            )
            session.add(file_record)
            await session.flush()

            # Сохраняем file_id в контексте
            context.user_data['pending_file_id'] = str(file_record.id)
            context.user_data['user_id'] = str(user.id)

        # Предлагаем выбрать формат
        await update.message.reply_text(
            f"✅ Файл '{document.file_name}' получен!\n\n"
            f"Размер: {size / 1024 / 1024:.1f} МБ\n"
            "Выберите формат для конвертации:",
            reply_markup=get_format_keyboard()
        )

    except Exception as e:
        logger.error(f"Failed to process file: {e}", exc_info=True)
        await update.message.reply_text("❌ Ошибка при обработке файла. Попробуйте еще раз.")
    finally:
        # Удаляем временный файл
        tmp_path.unlink(missing_ok=True)


async def handle_format_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle format selection from inline keyboard.
    Creates conversion job and starts Celery task.
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    if not callback_data or not callback_data.startswith('format_'):
        return

    output_format = callback_data.replace('format_', '')

    # Проверяем формат
    if output_format not in SUPPORTED_FORMATS:
        await query.edit_message_text(f"❌ Неподдерживаемый формат: {output_format}")
        return

    # Получаем данные из контекста
    file_id = context.user_data.get('pending_file_id')
    user_id = context.user_data.get('user_id')

    if not file_id or not user_id:
        await query.edit_message_text(
            "❌ Сессия истекла. Пожалуйста, отправьте файл снова."
        )
        context.user_data.clear()
        return

    # Обновляем сообщение
    await query.edit_message_text(
        f"🔄 Конвертирую в формат {output_format.upper()}...\n"
        "Это может занять несколько секунд."
    )

    try:
        # Создаём задачу конвертации
        async with AsyncSessionLocal() as session:
            job = ConversionJob(
                user_id=UUID(user_id),
                target_format=output_format,
                source_file_id=UUID(file_id),
                status=JobStatus.PENDING,
            )
            session.add(job)
            await session.flush()
            job_id = str(job.id)

        # Запускаем Celery задачу
        run_conversion.delay(job_id)

        # Отправляем пользователю ID задачи
        await query.message.reply_text(
            f"✅ Задача создана!\n\n"
            f"ID задачи: `{job_id}`\n"
            f"Формат: PDF → {output_format.upper()}\n\n"
            f"Используйте /status {job_id} для проверки прогресса.",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Failed to create conversion job: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Ошибка при создании задачи:\n{str(e)}"
        )
    finally:
        context.user_data.clear()


async def cancel_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel pending conversion and clear context."""
    if 'pending_file_id' in context.user_data:
        context.user_data.clear()
        await update.message.reply_text("❌ Конвертация отменена.")
    else:
        await update.message.reply_text("ℹ️ Нет активных конвертаций для отмены.")
