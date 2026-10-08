"""Intervention workflow router."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.models import Intervention, InterventionStatus
from app.database.session import get_db

router = APIRouter(prefix="/interventions", tags=["interventions"])


class InterventionCreate(BaseModel):
    student_id: uuid.UUID
    examination_id: uuid.UUID | None = None
    recommendation_text: str
    trigger_evidence_ids: list[uuid.UUID] | None = None
    rule_version: str = "1.0"


class InterventionReview(BaseModel):
    action: str  # APPROVE | MODIFY | DISMISS
    dismissal_reason: str | None = None
    modified_text: str | None = None


@router.get("")
async def list_interventions(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = None,
    student_id: uuid.UUID | None = None,
):
    q = select(Intervention)
    if status:
        q = q.where(Intervention.status == status)
    if student_id:
        q = q.where(Intervention.student_id == student_id)
    r = await db.execute(q.order_by(Intervention.created_at.desc()))
    interventions = r.scalars().all()
    return [
        {
            "id": str(i.id),
            "student_id": str(i.student_id),
            "status": i.status.value,
            "recommendation_text": i.recommendation_text,
            "rule_version": i.rule_version,
            "created_at": i.created_at.isoformat(),
        }
        for i in interventions
    ]


@router.post("", status_code=201)
async def create_intervention(
    body: InterventionCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    iv = Intervention(
        student_id=body.student_id,
        examination_id=body.examination_id,
        recommendation_text=body.recommendation_text,
        trigger_evidence_ids=[str(e) for e in body.trigger_evidence_ids] if body.trigger_evidence_ids else None,
        rule_version=body.rule_version,
        faculty_user_id=current_user.id,
        status=InterventionStatus.SUGGESTED,
    )
    db.add(iv)
    await db.flush()
    return {"id": str(iv.id), "status": iv.status.value}


@router.patch("/{id}")
async def review_intervention(
    id: uuid.UUID,
    body: InterventionReview,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(select(Intervention).where(Intervention.id == id))
    iv = r.scalar_one_or_none()
    if not iv:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Intervention", id)

    action = body.action.upper()
    if action == "APPROVE":
        iv.status = InterventionStatus.APPROVED
    elif action == "MODIFY":
        iv.status = InterventionStatus.MODIFIED
        if body.modified_text:
            iv.modified_text = body.modified_text
    elif action == "DISMISS":
        if not body.dismissal_reason:
            from app.core.exceptions import ValidationError
            raise ValidationError("dismissal_reason is required when dismissing an intervention")
        iv.status = InterventionStatus.DISMISSED
        iv.dismissal_reason = body.dismissal_reason
    else:
        from app.core.exceptions import ValidationError
        raise ValidationError(f"Unknown action: {action}")

    iv.faculty_user_id = current_user.id
    iv.reviewed_at = datetime.now(tz=timezone.utc)
    await db.flush()
    return {"id": str(iv.id), "status": iv.status.value}
