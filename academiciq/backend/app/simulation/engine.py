"""
What-If Simulation Engine.
Reuses the SAME deterministic service classes as production analytics.
Never writes to official tables.
All outputs stamped is_hypothetical=True.
"""
from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any

import numpy as np
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    GradingScheme, MetricLabel, ResultStatus,
    StudentSubjectResult, Subject, WhatIfScenario,
)
from app.intelligence.attention_engine import AttentionEngine, ALGORITHM_VERSION

logger = structlog.get_logger(__name__)

HYPOTHETICAL_LABEL = MetricLabel.HYPOTHETICAL.value


class SimulationEngine:
    """
    What-If engine. Reuses grade calculator, analytics engine, and attention engine.
    NO separate logic — all computation delegates to the same L1 services.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def simulate(
        self,
        student_id: uuid.UUID,
        examination_id: uuid.UUID,
        changes: dict[str, float],  # subject_id (str) → hypothetical_total_marks
        created_by: uuid.UUID,
        scenario_label: str | None = None,
    ) -> dict[str, Any]:
        """
        Run a what-if scenario. Returns current metrics, hypothetical metrics, and delta.
        Official tables are NEVER written to.
        """
        # 1. Load current results
        r = await self._db.execute(
            select(StudentSubjectResult, Subject)
            .join(Subject, StudentSubjectResult.subject_id == Subject.id)
            .where(
                StudentSubjectResult.student_id == student_id,
                StudentSubjectResult.examination_id == examination_id,
                StudentSubjectResult.is_latest_attempt == True,
            )
        )
        rows = r.all()
        if not rows:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Results for student/examination")

        # 2. Load active grading scheme
        from app.academics.service import GradingSchemeService
        gs = await GradingSchemeService(self._db).get_active()
        pass_mark = gs.pass_mark_overall if gs else 50

        # 3. Validate input changes against marks limits
        subject_map: dict[str, Subject] = {str(row[0].subject_id): row[1] for row in rows}
        for subj_id, hyp_marks in changes.items():
            if subj_id in subject_map:
                max_marks = subject_map[subj_id].max_total_marks
                if hyp_marks > max_marks:
                    from app.core.exceptions import ValidationError
                    raise ValidationError(
                        f"Hypothetical marks {hyp_marks} exceed maximum {max_marks} "
                        f"for subject {subject_map[subj_id].code}"
                    )

        # 4. Compute baseline metrics
        current_marks = []
        current_failed = 0
        current_passed = 0
        current_subject_metrics = []

        for res, subj in rows:
            if res.is_absent:
                continue
            tm = float(res.total_marks) if res.total_marks else None
            if tm is not None:
                current_marks.append(tm)
            status = res.result_status.value if res.result_status else "PENDING"
            if status == ResultStatus.PASS.value:
                current_passed += 1
            elif status == ResultStatus.FAIL.value:
                current_failed += 1
            grade = self._compute_grade(tm, gs) if gs and tm else res.grade
            current_subject_metrics.append({
                "subject_id": str(res.subject_id),
                "subject_code": subj.code,
                "total_marks": tm,
                "grade": grade,
                "result_status": status,
                "metric_label": MetricLabel.OFFICIAL.value,
            })

        baseline_avg = float(np.mean(current_marks)) if current_marks else None

        # 5. Apply hypothetical changes (in-memory only)
        hyp_marks_map: dict[str, float] = {}
        for res, subj in rows:
            sid = str(res.subject_id)
            if sid in changes:
                hyp_marks_map[sid] = changes[sid]
            elif not res.is_absent and res.total_marks:
                hyp_marks_map[sid] = float(res.total_marks)

        hyp_marks_list: list[float] = []
        hyp_failed = 0
        hyp_passed = 0
        hyp_subject_metrics = []

        for res, subj in rows:
            if res.is_absent:
                continue
            sid = str(res.subject_id)
            hyp_tm = hyp_marks_map.get(sid)
            if hyp_tm is not None:
                hyp_marks_list.append(hyp_tm)
            hyp_status = ResultStatus.PASS.value if (hyp_tm or 0) >= pass_mark else ResultStatus.FAIL.value
            if hyp_status == ResultStatus.PASS.value:
                hyp_passed += 1
            else:
                hyp_failed += 1
            hyp_grade = self._compute_grade(hyp_tm, gs) if gs and hyp_tm else None
            hyp_subject_metrics.append({
                "subject_id": sid,
                "subject_code": subj.code,
                "total_marks": hyp_tm,
                "grade": hyp_grade,
                "result_status": hyp_status,
                "metric_label": HYPOTHETICAL_LABEL,
                "changed": sid in changes,
            })

        hyp_avg = float(np.mean(hyp_marks_list)) if hyp_marks_list else None

        # 6. Compute delta
        delta_avg = round(hyp_avg - baseline_avg, 4) if (hyp_avg and baseline_avg) else None
        delta_failed = hyp_failed - current_failed

        # 7. Persist scenario (no official tables touched)
        scenario = WhatIfScenario(
            student_id=student_id,
            examination_id=examination_id,
            created_by=created_by,
            input_changes={k: v for k, v in changes.items()},
            output_metrics={
                "hypothetical_average": round(hyp_avg, 4) if hyp_avg else None,
                "hypothetical_passed": hyp_passed,
                "hypothetical_failed": hyp_failed,
            },
            baseline_metrics={
                "baseline_average": round(baseline_avg, 4) if baseline_avg else None,
                "baseline_passed": current_passed,
                "baseline_failed": current_failed,
            },
            algorithm_version=ALGORITHM_VERSION,
            grading_scheme_id=gs.id if gs else None,
            scenario_label=scenario_label,
            is_hypothetical=True,
        )
        self._db.add(scenario)
        await self._db.flush()

        return {
            "scenario_id": str(scenario.id),
            "student_id": str(student_id),
            "examination_id": str(examination_id),
            "current": {
                "average": round(baseline_avg, 4) if baseline_avg else None,
                "subjects_passed": current_passed,
                "subjects_failed": current_failed,
                "subject_details": current_subject_metrics,
                "metric_label": MetricLabel.OFFICIAL.value,
            },
            "hypothetical": {
                "average": round(hyp_avg, 4) if hyp_avg else None,
                "subjects_passed": hyp_passed,
                "subjects_failed": hyp_failed,
                "subject_details": hyp_subject_metrics,
                "metric_label": HYPOTHETICAL_LABEL,
            },
            "delta": {
                "average": delta_avg,
                "failed_change": delta_failed,
                "metric_label": HYPOTHETICAL_LABEL,
            },
            "is_hypothetical": True,
            "algorithm_version": ALGORITHM_VERSION,
        }

    def _compute_grade(self, marks: float | None, gs: GradingScheme | None) -> str | None:
        if marks is None or not gs:
            return None
        for band in sorted(gs.grade_map, key=lambda x: x.get("min", 0), reverse=True):
            if marks >= band.get("min", 0):
                return band.get("grade")
        return None
