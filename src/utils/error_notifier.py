"""
Error notification utilities.
Sends error reports to developer via Telegram.
"""
import os
import traceback
import logging
from typing import Optional

import httpx

from .config import settings

logger = logging.getLogger(__name__)


async def notify_admin(
    error: Exception,
    context: str = "",
    bot_token: Optional[str] = None,
    admin_id: Optional[int] = None,
) -> bool:
    """
    Send error notification to developer via Telegram.
    
    Args:
        error: The exception that was raised
        context: Additional context about where the error occurred
        bot_token: Telegram bot token (defaults to TELEGRAM_BOT_TOKEN)
        admin_id: Admin's Telegram ID (defaults to ADMIN_TELEGRAM_ID)
    
    Returns:
        True if notification was sent, False otherwise
    
    Example:
        try:
            await some_operation()
        except Exception as e:
            await notify_admin(e, context="some_operation failed")
    """
    token = bot_token or settings.TELEGRAM_BOT_TOKEN
    admin = admin_id or settings.ADMIN_TELEGRAM_ID
    
    if not admin:
        logger.warning("ADMIN_TELEGRAM_ID not set, skipping error notification")
        return False
    
    # Формируем сообщение об ошибке
    trace = traceback.format_exc()
    # Обрезаем трейс до 3000 символов (лимит Telegram)
    trace = trace[:3000] if len(trace) > 3000 else trace
    
    text = (
        f"🔴 <b>Ошибка в PDF Converter</b>\n\n"
        f"<b>Контекст:</b> <code>{context}</code>\n\n"
        f"<b>Ошибка:</b> <pre>{str(error)[:500]}</pre>\n\n"
        f"<b>Traceback:</b>\n<pre>{trace}</pre>"
    )
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            response = await client.post(
                url,
                json={
                    "chat_id": admin,
                    "text": text,
                    "parse_mode": "HTML",
                },
            )
            if response.status_code == 200:
                logger.info(f"Error notification sent to admin {admin}")
                return True
            else:
                logger.error(f"Failed to send error notification: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return False


async def notify_startup(bot_token: Optional[str] = None, admin_id: Optional[int] = None) -> bool:
    """
    Send notification about application startup.
    
    Args:
        bot_token: Telegram bot token
        admin_id: Admin's Telegram ID
    
    Returns:
        True if notification was sent, False otherwise
    """
    token = bot_token or settings.TELEGRAM_BOT_TOKEN
    admin = admin_id or settings.ADMIN_TELEGRAM_ID
    
    if not admin:
        return False
    
    text = (
        f"🟢 <b>PDF Converter запущен</b>\n\n"
        f"<b>Режим:</b> {'Development' if settings.DEBUG else 'Production'}\n"
        f"<b>Host:</b> {settings.API_HOST}:{settings.API_PORT}"
    )
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            response = await client.post(
                url,
                json={
                    "chat_id": admin,
                    "text": text,
                    "parse_mode": "HTML",
                },
            )
            return response.status_code == 200
    except Exception:
        return False
