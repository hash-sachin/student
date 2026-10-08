"""ML layer router — gated by data thresholds (Section 10)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.ml.service import MLService

router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/status")
async def ml_status(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Check whether the ML layer is activated.
    Returns 'ML disabled: insufficient data' until all thresholds are met.
    Thresholds: >= 500 records, >= 3 semesters, >= 50 positive-class examples.
    """
    svc = MLService(db)
    return await svc.get_status()
