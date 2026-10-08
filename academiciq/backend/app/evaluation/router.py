"""Evaluation framework router — H1-H8 hypothesis tracking."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.models import EvaluationRun
from app.database.session import get_db

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

HYPOTHESES = {
    "H1": "Document pipeline accuracy >= 98% on golden PDFs; zero silent drops",
    "H2": "Student matching: 0 false positives; all unmatched surfaced",
    "H3": "Analytics correctness: 100% match vs. reference calculation",
    "H4": "Attention scoring: 100% reproducible; sensitivity + fairness reports",
    "H5": "Evidence graph: 100% of insights resolvable to source PDF",
    "H6": "AI grounding: 100% numeric claims verified on >= 50 insights",
    "H7": "Interventions usability: faculty study completed; SUS >= 68",
    "H8": "Scale: dashboards < 2s p95 at 1,000 students x 8 semesters",
}


class RunEvaluationRequest(BaseModel):
    hypothesis_id: str
    run_config: dict | None = None
    notes: str | None = None


@router.get("/runs")
async def list_evaluation_runs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    r = await db.execute(
        select(EvaluationRun).order_by(EvaluationRun.run_at.desc()).limit(100)
    )
    runs = r.scalars().all()
    return [
        {
            "id": str(r.id),
            "hypothesis_id": r.hypothesis_id,
            "hypothesis_description": HYPOTHESES.get(r.hypothesis_id, "Unknown"),
            "passed": r.passed,
            "run_at": r.run_at.isoformat(),
            "notes": r.notes,
        }
        for r in runs
    ]


@router.post("/run")
async def run_evaluation(
    body: RunEvaluationRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Run an evaluation hypothesis check."""
    if body.hypothesis_id not in HYPOTHESES:
        from app.core.exceptions import ValidationError
        raise ValidationError(f"Unknown hypothesis: {body.hypothesis_id}. Valid: {list(HYPOTHESES)}")

    from app.evaluation.runner import EvaluationRunner
    runner = EvaluationRunner(db)
    results = await runner.run(body.hypothesis_id, body.run_config or {})

    run = EvaluationRun(
        hypothesis_id=body.hypothesis_id,
        run_config=body.run_config,
        results=results,
        passed=results.get("passed"),
        run_by=current_user.id,
        notes=body.notes,
    )
    db.add(run)
    await db.flush()

    return {
        "id": str(run.id),
        "hypothesis_id": run.hypothesis_id,
        "hypothesis_description": HYPOTHESES[body.hypothesis_id],
        "results": results,
        "passed": results.get("passed"),
    }
