from celery import Celery
from celery.schedules import crontab

from ..config import settings

celery_app = Celery(
    "pdf_converter",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.convert_task"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,          # re-queue on worker crash
    worker_prefetch_multiplier=1, # one task at a time per worker
    result_expires=3600,
)

# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "cleanup-expired-files": {
        "task": "app.tasks.convert_task.cleanup_expired_files_task",
        "schedule": crontab(minute=0, hour="*/6"),  # every 6 hours
    },
    "aggregate-daily-stats": {
        "task": "app.tasks.convert_task.aggregate_stats_task",
        "schedule": crontab(minute=0, hour=3),       # daily at 03:00 UTC
    },
}
