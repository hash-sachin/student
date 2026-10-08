"""
Celery task wrappers for PDF processing pipeline.
These wrap the pipeline logic in app.results.pipeline so it can be
dispatched as a Celery background task OR as a FastAPI BackgroundTask.
"""
from __future__ import annotations

import structlog

from app.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="app.tasks.pdf_processing.process_upload",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_upload(self, upload_id: str) -> dict:
    """
    Celery task: process a single uploaded PDF through the full pipeline.
    Calls app.results.pipeline.process_upload_pipeline via asyncio.
    """
    import asyncio
    from app.results.pipeline import process_upload_pipeline

    try:
        asyncio.run(process_upload_pipeline(upload_id=upload_id))
        return {"status": "completed", "upload_id": upload_id}
    except Exception as exc:
        logger.error("celery_task_failed", upload_id=upload_id, error=str(exc))
        raise self.retry(exc=exc)
