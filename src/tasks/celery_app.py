"""
Celery application configuration.
Sets up task queue, broker, and scheduled tasks.
"""
from celery import Celery
from celery.schedules import crontab

from ..config import settings

celery_app = Celery(
    "pdf_converter",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.tasks.convert_task"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,          # Re-queue on worker crash
    worker_prefetch_multiplier=1, # One task at a time per worker
    result_expires=3600,
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Очистка просроченных файлов каждые 6 часов
    "cleanup-expired-files": {
        "task": "src.tasks.convert_task.cleanup_expired_files_task",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # Агрегация статистики ежедневно в 03:00 UTC
    "aggregate-daily-stats": {
        "task": "src.tasks.convert_task.aggregate_stats_task",
        "schedule": crontab(minute=0, hour=3),
    },
}
