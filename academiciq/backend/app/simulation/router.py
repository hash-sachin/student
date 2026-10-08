"""What-If Simulation router."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.models import WhatIfScenario
from app.database.session import get_db
from app.simulation.engine import SimulationEngine

router = APIRouter(prefix="/simulation", tags=["simulation"])

HYPOTHETICAL_BANNER = "HYPOTHETICAL SCENARIO - NOT AN ACTUAL RESULT"


class SubjectChange(BaseModel):
    subject_id: uuid.UUID
    hypothetical_total_marks: float

    @field_validator("hypothetical_total_marks")
    @classmethod
    def marks_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Marks cannot be negative")
        return v


class WhatIfRequest(BaseModel):
    student_id: uuid.UUID
    examination_id: uuid.UUID
    changes: list[SubjectChange]
    scenario_label: str | None = None


@router.post("/what-if")
async def run_what_if(
    body: WhatIfRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Run a what-if simulation. Official tables are never modified.
    ALL outputs are labeled HYPOTHETICAL.
    """
    engine = SimulationEngine(db)
    result = await engine.simulate(
        student_id=body.student_id,
        examination_id=body.examination_id,
        changes={str(c.subject_id): c.hypothetical_total_marks for c in body.changes},
        created_by=current_user.id,
        scenario_label=body.scenario_label,
    )
    # Enforce hypothetical banner on every response
    result["hypothetical_banner"] = HYPOTHETICAL_BANNER
    result["is_hypothetical"] = True
    return result


@router.get("/{id}")
async def get_scenario(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(select(WhatIfScenario).where(WhatIfScenario.id == id))
    scenario = r.scalar_one_or_none()
    if not scenario:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("WhatIfScenario", id)
    return {
        "id": str(scenario.id),
        "student_id": str(scenario.student_id),
        "examination_id": str(scenario.examination_id),
        "input_changes": scenario.input_changes,
        "output_metrics": scenario.output_metrics,
        "baseline_metrics": scenario.baseline_metrics,
        "algorithm_version": scenario.algorithm_version,
        "scenario_label": scenario.scenario_label,
        "hypothetical_banner": HYPOTHETICAL_BANNER,
        "is_hypothetical": True,
        "created_at": scenario.created_at.isoformat(),
    }
