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

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await init_db()

    tg_app = build_application()
    await tg_app.initialize()

    if settings.TELEGRAM_WEBHOOK_URL:
        await set_webhook(f"{settings.TELEGRAM_WEBHOOK_URL}/api/v1/telegram/webhook")

    yield

    logger.info("Shutting down...")
    await tg_app.shutdown()
    await close_db()


app = FastAPI(
    title="PDF Converter Bot API",
    description="Telegram + Web PDF conversion service",
    version="1.0.0",
    lifespan=lifespan,
)

# State for slowapi
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(conversions.router, prefix=PREFIX)
app.include_router(files.router, prefix=PREFIX)
app.include_router(telegram.router, prefix=PREFIX)


@app.get("/")
async def root():
    return {"service": "PDF Converter Bot API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
