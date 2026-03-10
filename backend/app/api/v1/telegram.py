import logging

from fastapi import APIRouter, Request, HTTPException
from telegram import Update

from ...services.telegram_bot import get_application

router = APIRouter(prefix="/telegram", tags=["telegram"])
logger = logging.getLogger(__name__)


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Receive updates from Telegram via webhook."""
    try:
        data = await request.json()
        application = get_application()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return {"ok": True}
    except Exception as exc:
        logger.error(f"Webhook processing error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Webhook processing failed")
