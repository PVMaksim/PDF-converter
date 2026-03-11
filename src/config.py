"""
Application configuration.
All settings are loaded from environment variables only.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # =========================================================================
    # App settings
    # =========================================================================
    SECRET_KEY: str
    DEBUG: bool = False
    ALLOWED_HOSTS: str = "*"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False

    # =========================================================================
    # Database settings
    # =========================================================================
    DATABASE_URL: str
    DB_ECHO: bool = False

    # =========================================================================
    # Telegram settings
    # =========================================================================
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    ADMIN_TELEGRAM_ID: Optional[int] = None  # Для уведомлений об ошибках

    # =========================================================================
    # Redis / Celery settings
    # =========================================================================
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # =========================================================================
    # MinIO / S3 storage settings
    # =========================================================================
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "pdf-converter"
    MINIO_SECURE: bool = False

    # =========================================================================
    # Gotenberg settings
    # =========================================================================
    GOTENBERG_URL: str = "http://gotenberg:3000"

    # =========================================================================
    # File limits — free tier
    # =========================================================================
    MAX_FILE_SIZE_FREE_MB: int = 50
    FILE_TTL_FREE_HOURS: int = 24
    RATE_LIMIT_FREE_PER_HOUR: int = 10

    # =========================================================================
    # File limits — pro tier
    # =========================================================================
    MAX_FILE_SIZE_PRO_MB: int = 200
    FILE_TTL_PRO_DAYS: int = 7
    RATE_LIMIT_PRO_PER_HOUR: int = 100

    # =========================================================================
    # Local fallback storage (development only)
    # =========================================================================
    UPLOAD_DIR: str = "src/static/uploads"
    OUTPUT_DIR: str = "src/static/outputs"
    USE_LOCAL_STORAGE: bool = False  # Переключатель для fallback

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
