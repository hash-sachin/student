"""Pydantic schemas for result uploads and validation."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class UploadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    file_name: str
    file_hash: str
    file_size_bytes: int
    processing_status: str
    validation_status: str | None
    record_count: int | None
    valid_count: int | None
    warning_count: int | None
    error_count: int | None
    unmatched_count: int | None
    parser_name: str | None
    parser_version: str | None
    parser_confidence: float | None
    uploaded_by: uuid.UUID
    created_at: datetime


class StagedRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    raw_register_number: str | None
    raw_subject_code: str | None
    raw_subject_name: str | None
    raw_internal_marks: str | None
    raw_external_marks: str | None
    raw_total_marks: str | None
    raw_grade: str | None
    raw_result_status: str | None
    student_id: uuid.UUID | None
    subject_id: uuid.UUID | None
    internal_marks: float | None
    external_marks: float | None
    total_marks: float | None
    grade: str | None
    result_status: str | None
    is_absent: bool
    validation_status: str
    validation_notes: str | None
    error_reason: str | None
    admin_note: str | None
    confidence_score: float | None
    page_number: int | None
    extraction_method: str | None


class StagedRecordUpdate(BaseModel):
    student_id: uuid.UUID | None = None
    subject_id: uuid.UUID | None = None
    internal_marks: float | None = None
    external_marks: float | None = None
    total_marks: float | None = None
    grade: str | None = None
    result_status: str | None = None
    admin_note: str | None = None
    is_skipped: bool | None = None
    skip_reason: str | None = None


class ValidationPreviewResponse(BaseModel):
    upload_id: uuid.UUID
    total: int
    valid: int
    warning: int
    error: int
    unmatched: int
    duplicate: int
    skipped: int
    records: list[StagedRecordRead]


class CommitResponse(BaseModel):
    upload_id: uuid.UUID
    committed_count: int
    skipped_count: int
    status: str
