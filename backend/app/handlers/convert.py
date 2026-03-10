from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Optional
import logging
from pathlib import Path
from datetime import datetime

from ..database import get_db
from ..models.conversion_job import ConversionJob, JobStatus
from ..services.file_converter import FileConverter, OutputFormat
from ..services.file_storage import FileStorage

logger = logging.getLogger(__name__)

# Keyboard for format selection
def get_format_keyboard():
    """Create inline keyboard with supported output formats"""
    formats = [
        [("📄 DOCX", "docx"), ("📊 XLSX", "xlsx")],
        [("📈 PPTX", "pptx"), ("📝 TXT", "txt")],
        [("🖼️ JPEG", "jpeg"), ("🖼️ PNG", "png")],
        [("🌐 HTML", "html"), ("📋 RTF", "rtf")],
    ]
    keyboard = [
        [InlineKeyboardButton(text, callback_data=f"format_{data}")]
        for row in formats
        for text, data in row
    ]
    return InlineKeyboardMarkup(keyboard)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming document (PDF file)
    """
    document = update.message.document
    user = update.effective_user

    # Check if it's a PDF
    if not document.file_name or not document.file_name.lower().endswith('.pdf'):
        await update.message.reply_text(
            "❌ Пожалуйста, отправьте PDF файл.\n"
            "Я поддерживаю только PDF для конвертации."
        )
        return

    # Download the file
    try:
        file = await document.get_file()
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        await update.message.reply_text("❌ Ошибка при получении файла. Попробуйте еще раз.")
        return

    # Save file temporarily
    storage = FileStorage()
    try:
        input_path, input_filename = await storage.save_upload_from_telegram(
            file.file_path,
            user.id,
            document.file_name
        )
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении файла.")
        return

    # Store in user context for later
    context.user_data['pending_conversion'] = {
        'input_path': input_path,
        'input_filename': input_filename,
        'user_id': user.id,
    }

    # Ask for output format
    await update.message.reply_text(
        f"✅ Файл '{document.file_name}' получен!\n\n"
        "Выберите формат для конвертации:",
        reply_markup=get_format_keyboard()
    )


async def handle_format_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle format selection from inline keyboard
    """
    query = update.callback_query
    await query.answer()

    # Extract format from callback data
    callback_data = query.data
    if not callback_data.startswith('format_'):
        return

    output_format = callback_data.replace('format_', '')

    # Get pending conversion data
    pending = context.user_data.get('pending_conversion')
    if not pending:
        await query.edit_message_text(
            "❌ Сессия истекла. Пожалуйста, отправьте файл снова."
        )
        return

    # Validate format
    try:
        output_format_enum = OutputFormat(output_format)
    except ValueError:
        await query.edit_message_text(f"❌ Неподдерживаемый формат: {output_format}")
        return

    # Update message
    await query.edit_message_text(
        f"🔄 Конвертирую в формат {output_format.upper()}...\n"
        "Это может занять несколько секунд."
    )

    # Start conversion
    converter = FileConverter()
    storage = FileStorage()
    user_id = pending['user_id']
    input_path = pending['input_path']
    input_filename = pending['input_filename']

    # Create job record in DB
    async with get_db() as db:
        job = ConversionJob(
            user_id=user_id,
            input_filename=input_filename,
            input_format="pdf",
            output_format=output_format,
            status=JobStatus.PROCESSING,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        try:
            # Convert
            result = await converter.convert_pdf(
                input_path,
                output_format_enum,
                start_page=0,
                end_page=None,
            )

            if result["success"]:
                job.status = JobStatus.COMPLETED
                job.output_filename = Path(result["output_path"]).name
                job.completed_at = datetime.utcnow()
                await db.commit()

                # Send result file to user
                output_path = Path(result["output_path"])
                if output_path.exists():
                    with open(output_path, 'rb') as f:
                        await query.message.reply_document(
                            document=f,
                            filename=output_path.name,
                            caption=f"✅ Конвертация завершена!\nФормат: {output_format.upper()}"
                        )

                    # Cleanup input file
                    storage.delete_file(input_path)
                else:
                    await query.edit_message_text("❌ Файл не был создан.")
            else:
                job.status = JobStatus.FAILED
                job.error_message = result["error"]
                await db.commit()
                await query.edit_message_text(
                    f"❌ Ошибка конвертации:\n{result['error']}"
                )

        except Exception as e:
            logger.error(f"Conversion failed: {e}", exc_info=True)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            await db.commit()
            await query.edit_message_text(f"❌ Неожиданная ошибка: {str(e)}")

    # Clear pending conversion
    if 'pending_conversion' in context.user_data:
        del context.user_data['pending_conversion']


async def cancel_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancel pending conversion
    """
    pending = context.user_data.get('pending_conversion')
    if pending:
        storage = FileStorage()
        storage.delete_file(pending['input_path'])
        del context.user_data['pending_conversion']
        await update.message.reply_text("❌ Конвертация отменена.")
    else:
        await update.message.reply_text("ℹ️ Нет активных конвертаций для отмены.")