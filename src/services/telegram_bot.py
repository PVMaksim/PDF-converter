"""
Telegram bot application builder.
Configures handlers and initializes the bot.
"""
import logging
from typing import Any

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from ..config import settings

logger = logging.getLogger(__name__)

_application: Application | None = None


def get_application() -> Application:
    """
    Get the Telegram bot Application instance.
    
    Raises:
        RuntimeError: If application was not initialized with build_application()
    """
    if _application is None:
        raise RuntimeError("Telegram application not initialized. Call build_application() first.")
    return _application


def build_application() -> Application:
    """
    Build and configure the Telegram bot Application.
    Registers all command and message handlers.
    
    Returns:
        Configured telegram.ext.Application instance
    """
    global _application

    from ..handlers.start import start_command, help_command
    from ..handlers.convert import document_handler, handle_format_selection
    from ..handlers.status import status_handler
    from ..handlers.admin import stats_command, cleanup_command

    # Создаём приложение
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("cleanup", cleanup_command))

    # Регистрием обработчик документов (PDF)
    app.add_handler(MessageHandler(filters.Document.PDF, document_handler))

    # Регистрируем обработчик callback query для выбора формата
    app.add_handler(CallbackQueryHandler(handle_format_selection, pattern=r'^format_'))

    # Обработчик неизвестных команд
    app.add_handler(MessageHandler(filters.COMMAND, unknown_handler))

    _application = app
    logger.info("Telegram bot application built")
    return app


async def set_webhook(url: str):
    """
    Set Telegram webhook.
    
    Args:
        url: Full webhook URL (e.g., https://yourdomain.com/api/v1/telegram/webhook)
    """
    app = get_application()
    await app.bot.set_webhook(url=url)
    logger.info(f"Webhook set to: {url}")


async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands."""
    await update.message.reply_text(
        "❓ Неизвестная команда. Используйте /help для списка доступных команд."
    )
