"""Result upload service — file validation, storage, background processing coordination."""
from __future__ import annotations

import hashlib
import io
import os
import uuid
from pathlib import Path
from typing import Sequence

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AlreadyExistsError, DuplicateUploadError, NotFoundError, ValidationError
)
from app.database.models import (
    ExtractedRecordStaging, ResultProcessingLog, ResultUpload,
    StudentSubjectResult, UploadProcessingStatus, ValidationRecordStatus
)
# pipeline is imported lazily inside initiate_upload to avoid pdfplumber at startup
import structlog

logger = structlog.get_logger(__name__)

ALLOWED_MAGIC_BYTES = {b"%PDF"}  # PDF magic bytes


class ResultUploadService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def initiate_upload(
        self,
        file: UploadFile,
        uploaded_by: uuid.UUID,
        semester_id: uuid.UUID | None,
        examination_id: uuid.UUID | None,
        background_tasks: BackgroundTasks,
        hash_override_reason: str | None = None,
    ) -> ResultUpload:
        # 1. Size limit check
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.MAX_UPLOAD_SIZE_MB:
            raise ValidationError(
                f"File size {size_mb:.1f}MB exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
            )

        # 2. Extension check
        filename = file.filename or "upload.pdf"
        suffix = Path(filename).suffix.lower()
        if suffix not in settings.ALLOWED_EXTENSIONS:
            raise ValidationError(f"File type '{suffix}' not allowed. Only PDF is accepted.")

        # 3. Magic bytes check (PDF: %PDF)
        if not content[:4] in ALLOWED_MAGIC_BYTES:
            raise ValidationError("File is not a valid PDF (magic bytes check failed)")

        # 4. SHA-256 hash
        file_hash = hashlib.sha256(content).hexdigest()

        # 5. Duplicate hash check
        existing = await self._db.execute(
            select(ResultUpload).where(
                ResultUpload.file_hash == file_hash,
                ResultUpload.is_active == True,
            )
        )
        existing_upload = existing.scalar_one_or_none()
        if existing_upload and not hash_override_reason:
            raise DuplicateUploadError(
                f"A file with this hash already exists (upload_id={existing_upload.id}). "
                "Provide hash_override_reason to force re-upload."
            )

        # 6. Store file (hashed filename, outside web root)
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        stored_filename = f"{file_hash}.pdf"
        file_path = upload_dir / stored_filename
        file_path.write_bytes(content)

        # 7. Create upload record
        upload = ResultUpload(
            file_name=filename,
            file_hash=file_hash,
            file_path=str(file_path),
            file_size_bytes=len(content),
            semester_id=semester_id,
            examination_id=examination_id,
            uploaded_by=uploaded_by,
            processing_status=UploadProcessingStatus.QUEUED,
            hash_override_reason=hash_override_reason,
        )
        self._db.add(upload)
        await self._db.flush()
        upload_id = upload.id

        logger.info("upload_initiated", upload_id=str(upload_id), file=filename, size_mb=round(size_mb, 2))

        # 8. Queue background processing (lazy import of pipeline)
        from app.results.pipeline import process_upload_pipeline
        background_tasks.add_task(process_upload_pipeline, upload_id=str(upload_id))

        return upload

    async def list_uploads(self) -> Sequence[ResultUpload]:
        r = await self._db.execute(
            select(ResultUpload).order_by(ResultUpload.created_at.desc())
        )
        return r.scalars().all()

    async def get_upload(self, id: uuid.UUID) -> ResultUpload:
        r = await self._db.execute(select(ResultUpload).where(ResultUpload.id == id))
        u = r.scalar_one_or_none()
        if not u:
            raise NotFoundError("ResultUpload", id)
        return u

    async def get_validation_preview(self, id: uuid.UUID):
        from app.results.schemas import ValidationPreviewResponse, StagedRecordRead
        upload = await self.get_upload(id)

        r = await self._db.execute(
            select(ExtractedRecordStaging).where(ExtractedRecordStaging.upload_id == id)
        )
        records = r.scalars().all()

        counts: dict[str, int] = {s.value: 0 for s in ValidationRecordStatus}
        for rec in records:
            counts[rec.validation_status.value] = counts.get(rec.validation_status.value, 0) + 1

        return ValidationPreviewResponse(
            upload_id=id,
            total=len(records),
            valid=counts.get("VALID", 0),
            warning=counts.get("WARNING", 0),
            error=counts.get("ERROR", 0),
            unmatched=counts.get("UNMATCHED", 0),
            duplicate=counts.get("DUPLICATE", 0),
            skipped=counts.get("SKIPPED", 0),
            records=[StagedRecordRead.model_validate(r) for r in records],
        )

    async def update_staged_record(
        self, upload_id: uuid.UUID, record_id: uuid.UUID, data: dict
    ) -> ExtractedRecordStaging:
        r = await self._db.execute(
            select(ExtractedRecordStaging).where(
                ExtractedRecordStaging.id == record_id,
                ExtractedRecordStaging.upload_id == upload_id,
            )
        )
        rec = r.scalar_one_or_none()
        if not rec:
            raise NotFoundError("StagedRecord", record_id)
        for k, v in data.items():
            setattr(rec, k, v)
        await self._db.flush()
        return rec

    async def commit_upload(self, upload_id: uuid.UUID, committed_by: uuid.UUID):
        from app.results.schemas import CommitResponse
        upload = await self.get_upload(upload_id)

        if upload.processing_status != UploadProcessingStatus.READY_FOR_REVIEW:
            raise ValidationError(
                f"Upload is not ready for commit (status={upload.processing_status})"
            )

        # Get all non-skipped VALID/WARNING records
        r = await self._db.execute(
            select(ExtractedRecordStaging).where(
                ExtractedRecordStaging.upload_id == upload_id,
                ExtractedRecordStaging.is_skipped == False,
                ExtractedRecordStaging.validation_status.in_([
                    ValidationRecordStatus.VALID,
                    ValidationRecordStatus.WARNING,
                ]),
                ExtractedRecordStaging.student_id.isnot(None),
                ExtractedRecordStaging.subject_id.isnot(None),
            )
        )
        staged = r.scalars().all()

        # Get active grading scheme
        from app.academics.service import GradingSchemeService
        gs_svc = GradingSchemeService(self._db)
        gs = await gs_svc.get_active()
        if not gs:
            raise ValidationError("No active grading scheme configured")

        # Commit to official table
        committed = 0
        for rec in staged:
            result = StudentSubjectResult(
                student_id=rec.student_id,
                subject_id=rec.subject_id,
                examination_id=upload.examination_id,
                upload_id=upload_id,
                grading_scheme_id=gs.id,
                internal_marks=rec.internal_marks,
                external_marks=rec.external_marks,
                total_marks=rec.total_marks,
                grade=rec.grade,
                result_status=rec.result_status or "PENDING",
                is_absent=rec.is_absent,
                special_code=rec.special_code,
                staging_record_id=rec.id,
            )
            self._db.add(result)
            committed += 1

        upload.processing_status = UploadProcessingStatus.COMMITTED
        await self._db.flush()

        skipped_r = await self._db.execute(
            select(func.count()).select_from(ExtractedRecordStaging).where(
                ExtractedRecordStaging.upload_id == upload_id,
                ExtractedRecordStaging.is_skipped == True,
            )
        )
        skipped = skipped_r.scalar_one()

        logger.info("upload_committed", upload_id=str(upload_id), committed=committed, skipped=skipped)

        return CommitResponse(
            upload_id=upload_id,
            committed_count=committed,
            skipped_count=skipped,
            status="COMMITTED",
        )

    async def reject_upload(
        self, upload_id: uuid.UUID, rejected_by: uuid.UUID, reason: str | None
    ) -> dict:
        upload = await self.get_upload(upload_id)
        upload.processing_status = UploadProcessingStatus.REJECTED
        await self._db.flush()
        logger.info("upload_rejected", upload_id=str(upload_id), reason=reason)
        return {"upload_id": str(upload_id), "status": "REJECTED"}
