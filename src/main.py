"""
PDF Converter Bot API — Main entry point.
FastAPI application with Telegram bot integration.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from .config import settings
from .database import init_db, close_db
from .middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from .api.v1 import auth, conversions, files, telegram
from .services.telegram_bot import build_application, set_webhook
from .utils.error_notifier import notify_admin, notify_startup

# Настраиваем логирование
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — startup and shutdown."""
    logger.info("Starting up PDF Converter Bot API...")
    
    # Инициализация БД
    await init_db()
    
    # Инициализация Telegram бота
    tg_app = build_application()
    await tg_app.initialize()
    
    # Установка webhook (если указан URL)
    if settings.TELEGRAM_WEBHOOK_URL:
        try:
            await set_webhook(f"{settings.TELEGRAM_WEBHOOK_URL}/api/v1/telegram/webhook")
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            await notify_admin(e, context="Webhook setup failed")
    
    # Уведомление о запуске
    if settings.ADMIN_TELEGRAM_ID:
        await notify_startup()
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await tg_app.shutdown()
    await close_db()


app = FastAPI(
    title="PDF Converter Bot API",
    description="Telegram + Web PDF conversion service",
    version="2.0.0",
    lifespan=lifespan,
)

# Инициализация rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS.split(",") if settings.ALLOWED_HOSTS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX, tags=["auth"])
app.include_router(conversions.router, prefix=PREFIX, tags=["conversions"])
app.include_router(files.router, prefix=PREFIX, tags=["files"])
app.include_router(telegram.router, prefix=PREFIX, tags=["telegram"])


@app.get("/")
async def root():
    """Root endpoint — API info."""
    return {
        "service": "PDF Converter Bot API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler.
    Logs the error and notifies admin via Telegram.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Уведомляем админа об ошибке
    if settings.ADMIN_TELEGRAM_ID:
        await notify_admin(
            exc,
            context=f"Unhandled exception on {request.url.path}",
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
