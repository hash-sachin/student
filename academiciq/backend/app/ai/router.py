"""AI Insights router with full guardrail pipeline."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.ai.service import AIInsightService

router = APIRouter(prefix="/ai", tags=["ai"])


class GenerateInsightRequest(BaseModel):
    entity_type: str  # student | class | department
    entity_id: uuid.UUID
    examination_id: uuid.UUID | None = None


@router.get("/insights")
async def list_insights(
    entity_type: str,
    entity_id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.database.models import AIInsight
    r = await db.execute(
        select(AIInsight)
        .where(
            AIInsight.entity_type == entity_type,
            AIInsight.entity_id == entity_id,
            AIInsight.guardrail_passed == True,
        )
        .order_by(AIInsight.created_at.desc())
    )
    insights = r.scalars().all()
    return [
        {
            "id": str(i.id),
            "entity_type": i.entity_type,
            "entity_id": str(i.entity_id),
            "rendered_text": i.rendered_text,
            "evidence_ids": i.evidence_ids,
            "guardrail_passed": i.guardrail_passed,
            "is_fallback_template": i.is_fallback_template,
            "model_version": i.model_version,
            "created_at": i.created_at.isoformat(),
        }
        for i in insights
    ]


@router.post("/insights/generate")
async def generate_insight(
    body: GenerateInsightRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate an AI insight with full guardrail verification."""
    svc = AIInsightService(db)
    result = await svc.generate(
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        examination_id=body.examination_id,
        generated_by=current_user.id,
    )
    return result
