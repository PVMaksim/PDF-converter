import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from ..config import settings

logger = logging.getLogger(__name__)

_application: Application | None = None


def get_application() -> Application:
    global _application
    if _application is None:
        raise RuntimeError("Telegram application not initialized. Call build_application() first.")
    return _application


def build_application() -> Application:
    """Build and configure the telegram bot Application."""
    global _application

    from ..handlers.start import start_handler
    from ..handlers.convert import convert_handler, document_handler
    from ..handlers.status import status_handler
    from ..handlers.admin import admin_handler

    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("convert", convert_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("admin", admin_handler))
    app.add_handler(MessageHandler(filters.Document.PDF, document_handler))

    _application = app
    logger.info("Telegram bot application built")
    return app


async def set_webhook(url: str):
    app = get_application()
    await app.bot.set_webhook(url=url)
    logger.info(f"Webhook set to: {url}")
