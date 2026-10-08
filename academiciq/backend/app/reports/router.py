"""Reports router — PDF/Excel/CSV exports with watermarking."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.reports.generator import ReportGenerator

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/student/{id}")
async def student_report(
    id: uuid.UUID,
    format: str = "pdf",
    current_user: CurrentUser = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    gen = ReportGenerator(db)
    content, media_type, filename = await gen.student_report(
        id, format=format, requested_by=current_user.id
    )
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/class/{section_id}")
async def class_report(
    section_id: uuid.UUID,
    examination_id: uuid.UUID,
    format: str = "pdf",
    current_user: CurrentUser = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    gen = ReportGenerator(db)
    content, media_type, filename = await gen.class_report(
        section_id, examination_id, format=format, requested_by=current_user.id
    )
    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
