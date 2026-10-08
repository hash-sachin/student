"""Results API router — Phase 2 implementation."""
from __future__ import annotations

import hashlib
import io
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.results.service import ResultUploadService
from app.results.schemas import (
    UploadRead, ValidationPreviewResponse, StagedRecordUpdate, CommitResponse
)
from app.core.config import settings

router = APIRouter(prefix="/results", tags=["results"])


@router.post("/upload", response_model=UploadRead, status_code=202)
async def upload_result_pdf(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    semester_id: uuid.UUID | None = Form(None),
    examination_id: uuid.UUID | None = Form(None),
    hash_override_reason: str | None = Form(None),
):
    """
    Upload a result PDF. File is validated (magic bytes, size, hash dedup),
    stored, and queued for background parsing.
    """
    svc = ResultUploadService(db)
    return await svc.initiate_upload(
        file=file,
        uploaded_by=current_user.id,
        semester_id=semester_id,
        examination_id=examination_id,
        background_tasks=background_tasks,
        hash_override_reason=hash_override_reason,
    )


@router.get("/uploads", response_model=list[UploadRead])
async def list_uploads(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ResultUploadService(db)
    return await svc.list_uploads()


@router.get("/uploads/{id}", response_model=UploadRead)
async def get_upload(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ResultUploadService(db)
    return await svc.get_upload(id)


@router.get("/uploads/{id}/validation", response_model=ValidationPreviewResponse)
async def get_validation_preview(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ResultUploadService(db)
    return await svc.get_validation_preview(id)


@router.put("/uploads/{id}/records/{rid}", status_code=200)
async def update_staged_record(
    id: uuid.UUID,
    rid: uuid.UUID,
    body: StagedRecordUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ResultUploadService(db)
    return await svc.update_staged_record(id, rid, body.model_dump(exclude_none=True))


@router.post("/uploads/{id}/commit", response_model=CommitResponse)
async def commit_upload(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ResultUploadService(db)
    return await svc.commit_upload(id, committed_by=current_user.id)


@router.post("/uploads/{id}/reject", status_code=200)
async def reject_upload(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    reason: str | None = None,
):
    svc = ResultUploadService(db)
    return await svc.reject_upload(id, rejected_by=current_user.id, reason=reason)
