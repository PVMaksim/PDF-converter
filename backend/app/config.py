from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    SECRET_KEY: str = "change-me-in-production"
    DEBUG: bool = False
    ALLOWED_HOSTS: str = "*"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/pdf_bot"
    DB_ECHO: bool = False

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: Optional[str] = None

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # MinIO / S3
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "pdf-converter"
    MINIO_SECURE: bool = False

    # Gotenberg
    GOTENBERG_URL: str = "http://gotenberg:3000"

    # File limits — free tier
    MAX_FILE_SIZE_FREE_MB: int = 50
    FILE_TTL_FREE_HOURS: int = 24
    RATE_LIMIT_FREE_PER_HOUR: int = 10

    # File limits — pro tier
    MAX_FILE_SIZE_PRO_MB: int = 200
    FILE_TTL_PRO_DAYS: int = 7
    RATE_LIMIT_PRO_PER_HOUR: int = 100

    # Local fallback storage (dev)
    UPLOAD_DIR: str = "app/static/uploads"
    OUTPUT_DIR: str = "app/static/outputs"

    class Config:
        env_file = ".env"


settings = Settings()
