"""
Celery application configuration.
In local dev without Redis, Celery tasks are run via FastAPI BackgroundTasks instead.
"""
from __future__ import annotations

from app.core.config import settings

try:
    from celery import Celery

    celery_app = Celery(
        "academiciq",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["app.tasks.pdf_processing"],
    )
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )
except ImportError:
    # Celery not installed — tasks run via FastAPI BackgroundTasks
    celery_app = None  # type: ignore[assignment]
