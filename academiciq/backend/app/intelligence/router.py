"""Intelligence API router — attention, decline, improvement, top performers."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.intelligence.attention_engine import AttentionEngine, ALGORITHM_VERSION
from app.database.models import AcademicAttentionScore, AttentionBand

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/attention")
async def get_attention_list(
    examination_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    band: str | None = Query(None),
):
    """Return students flagged for academic attention for a given examination."""
    q = select(AcademicAttentionScore).where(
        AcademicAttentionScore.examination_id == examination_id,
        AcademicAttentionScore.algorithm_version == ALGORITHM_VERSION,
    )
    if band:
        q = q.where(AcademicAttentionScore.band == band)
    r = await db.execute(q.order_by(AcademicAttentionScore.raw_score.desc()))
    scores = r.scalars().all()

    return [
        {
            "student_id": str(s.student_id),
            "raw_score": float(s.raw_score),
            "band": s.band.value,
            "is_partial_score": s.is_partial_score,
            "missing_factors": s.missing_factors,
            "algorithm_version": s.algorithm_version,
            "metric_label": "ESTIMATED",
            "calculation_timestamp": s.calculation_timestamp.isoformat(),
        }
        for s in scores
    ]


@router.post("/attention/compute/{student_id}")
async def compute_attention_score(
    student_id: uuid.UUID,
    examination_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    section_id: uuid.UUID | None = None,
):
    """Compute (or recompute) the attention score for a student."""
    engine = AttentionEngine(db)
    result = await engine.compute(student_id, examination_id, section_id=section_id)
    return {
        "student_id": str(result.student_id),
        "examination_id": str(result.examination_id),
        "raw_score": result.raw_score,
        "band": result.band.value,
        "is_partial_score": result.is_partial_score,
        "missing_factors": result.missing_factors,
        "factors": [
            {
                "id": f.factor_id,
                "name": f.factor_name,
                "raw_value": f.raw_value,
                "points": f.points,
                "max_points": f.max_points,
                "evidence": f.evidence,
                "skipped": f.skipped,
                "skip_reason": f.skip_reason,
            }
            for f in result.factors
        ],
        "algorithm_version": result.algorithm_version,
        "metric_label": "ESTIMATED",
        "input_snapshot_hash": result.input_snapshot_hash,
    }
