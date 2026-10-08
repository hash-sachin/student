"""Longitudinal Academic Profile router."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.profile.service import ProfileService

router = APIRouter(tags=["profile"])


@router.get("/profile/student/{id}")
@router.get("/digital-twin/student/{id}")
async def get_student_profile(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Returns the Longitudinal Academic Profile for a student.
    Includes: timeline, subject results, metrics, attention scores,
    detected patterns (decline/improvement), evidence root IDs.
    'Academic Digital Twin' is a secondary alias per ADR-003.
    """
    svc = ProfileService(db)
    return await svc.get_longitudinal_profile(id)
