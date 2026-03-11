"""
Logging configuration.
Centralized logging setup for the application.
"""
import logging
import sys
from typing import Optional

from ..config import settings


def setup_logging(
    level: Optional[str] = None,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Log level (default from settings.DEBUG)
        log_format: Log message format
    
    Example:
        setup_logging()  # Use defaults
        setup_logging("DEBUG")  # Force debug level
    """
    # Определяем уровень логирования
    if level:
        log_level = getattr(logging, level.upper())
    else:
        log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Настраиваем root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        stream=sys.stdout,
    )
    
    # Устанавливаем уровни для шумных библиотек
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.DB_ECHO else logging.WARNING
    )
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    
    Example:
        logger = get_logger(__name__)
        logger.info("Message")
    """
    return logging.getLogger(name)
