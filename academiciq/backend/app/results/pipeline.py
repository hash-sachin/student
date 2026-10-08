"""
Document Intelligence Pipeline.
Orchestrates: PDF Analysis → Parser Selection → Extraction → Normalization
→ Validation → Staging store.

This runs as a background task (FastAPI BackgroundTasks or Celery).
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog

from app.core.config import settings
from app.database.session import AsyncSessionLocal
from app.database.models import (
    ExtractedRecordStaging, ResultProcessingLog, ResultUpload,
    UploadProcessingStatus, ValidationRecordStatus
)
# Lazy imports — pdfplumber/tesseract only loaded when a PDF is actually processed
# This allows the app to start without these optional system dependencies

logger = structlog.get_logger(__name__)


async def process_upload_pipeline(upload_id: str) -> None:
    """
    Full pipeline for one uploaded PDF.
    Stages: QUEUED → PROCESSING → VALIDATION → READY_FOR_REVIEW | FAILED
    """
    upload_uuid = uuid.UUID(upload_id)
    logger.info("pipeline_start", upload_id=upload_id)

    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select, update

            # Load upload record
            r = await db.execute(select(ResultUpload).where(ResultUpload.id == upload_uuid))
            upload = r.scalar_one_or_none()
            if not upload:
                logger.error("pipeline_upload_not_found", upload_id=upload_id)
                return

            # Stage: PROCESSING
            upload.processing_status = UploadProcessingStatus.PROCESSING
            await _log_stage(db, upload_uuid, "PROCESSING", "STARTED")
            await db.commit()

            # Select parser (lazy import — pdfplumber only needed here)
            from app.parsers.registry import ParserRegistry
            from app.validation.engine import ValidationEngine

            registry = ParserRegistry()
            parser = registry.select_parser(upload.file_path)

            await _log_stage(db, upload_uuid, "PARSING", "STARTED",
                             details={"parser": parser.name, "version": parser.version})

            # Extract records
            extracted = await asyncio.to_thread(parser.extract, upload.file_path)

            upload.parser_name = parser.name
            upload.parser_version = parser.version
            upload.parser_confidence = parser.last_confidence

            await _log_stage(db, upload_uuid, "PARSING", "COMPLETED",
                             details={"extracted_count": len(extracted)})

            # Stage: VALIDATION
            upload.processing_status = UploadProcessingStatus.VALIDATION
            await _log_stage(db, upload_uuid, "VALIDATION", "STARTED")
            await db.commit()

            engine = ValidationEngine(db)
            staged_records = await engine.validate_and_stage(upload_uuid, extracted)

            # Count statuses
            counts: dict[str, int] = {s.value: 0 for s in ValidationRecordStatus}
            for rec in staged_records:
                counts[rec.validation_status.value] = counts.get(rec.validation_status.value, 0) + 1

            upload.record_count = len(staged_records)
            upload.valid_count = counts.get("VALID", 0)
            upload.warning_count = counts.get("WARNING", 0)
            upload.error_count = counts.get("ERROR", 0)
            upload.unmatched_count = counts.get("UNMATCHED", 0)
            upload.processing_status = UploadProcessingStatus.READY_FOR_REVIEW
            upload.validation_status = "COMPLETED"

            await _log_stage(db, upload_uuid, "VALIDATION", "COMPLETED",
                             details=counts)
            await db.commit()

            logger.info("pipeline_complete", upload_id=upload_id, **counts)

        except Exception as e:
            logger.error("pipeline_failed", upload_id=upload_id, error=str(e))
            try:
                r2 = await db.execute(select(ResultUpload).where(ResultUpload.id == upload_uuid))
                u2 = r2.scalar_one_or_none()
                if u2:
                    u2.processing_status = UploadProcessingStatus.FAILED
                await _log_stage(db, upload_uuid, "PIPELINE", "FAILED", details={"error": str(e)})
                await db.commit()
            except Exception:
                pass


async def _log_stage(
    db,
    upload_id: uuid.UUID,
    stage: str,
    status: str,
    details: dict | None = None,
) -> None:
    log = ResultProcessingLog(
        upload_id=upload_id,
        stage=stage,
        status=status,
        message=f"{stage} {status}",
        details=details,
        finished_at=datetime.now(tz=timezone.utc) if status in ("COMPLETED", "FAILED") else None,
    )
    db.add(log)
