"""Analytics API router."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.engine import AnalyticsEngine
from app.auth.dependencies import CurrentUser
from app.database.session import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/student/{id}")
async def student_analytics(
    id: uuid.UUID,
    examination_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = AnalyticsEngine(db)
    return await engine.compute_student_semester_analytics(id, examination_id)


@router.get("/subject/{id}")
async def subject_analytics(
    id: uuid.UUID,
    examination_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = AnalyticsEngine(db)
    result = await engine.compute_subject_analytics(id, examination_id)
    # Don't return raw marks list in API response
    return {k: v for k, v in result.__dict__.items() if k != "marks"}


@router.get("/class/{section_id}")
async def class_analytics(
    section_id: uuid.UUID,
    examination_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = AnalyticsEngine(db)
    return await engine.compute_class_analytics(section_id, examination_id)


@router.get("/semester/compare")
async def semester_comparison(
    student_id: uuid.UUID,
    from_examination_id: uuid.UUID,
    to_examination_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    engine = AnalyticsEngine(db)
    return await engine.compute_semester_comparison(
        student_id, from_examination_id, to_examination_id
    )
