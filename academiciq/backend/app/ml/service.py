"""
ML Layer (Optional, Gated) — Phase 9.
Activation requires ALL of:
  - >= 500 student-semester records
  - >= 3 completed semesters
  - >= 50 positive-class examples
  - Independent ground truth (NOT rule engine output)

If thresholds not met, returns: "ML disabled: insufficient data"
"""
from __future__ import annotations

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import StudentSubjectResult

logger = structlog.get_logger(__name__)

ML_MIN_RECORDS = 500
ML_MIN_SEMESTERS = 3
ML_MIN_POSITIVE_CLASS = 50


class MLService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def check_activation_thresholds(self) -> dict:
        """Check whether ML activation thresholds are met."""
        r = await self._db.execute(select(func.count()).select_from(StudentSubjectResult))
        total_records = r.scalar_one()

        # Count distinct examinations
        from sqlalchemy import distinct
        r2 = await self._db.execute(
            select(func.count(distinct(StudentSubjectResult.examination_id)))
        )
        total_exams = r2.scalar_one()

        # Count failed subjects as proxy for positive class
        from app.database.models import ResultStatus
        r3 = await self._db.execute(
            select(func.count()).select_from(StudentSubjectResult).where(
                StudentSubjectResult.result_status == ResultStatus.FAIL
            )
        )
        positive_class = r3.scalar_one()

        meets_records = total_records >= ML_MIN_RECORDS
        meets_semesters = total_exams >= ML_MIN_SEMESTERS
        meets_positive = positive_class >= ML_MIN_POSITIVE_CLASS
        all_met = meets_records and meets_semesters and meets_positive

        return {
            "ml_enabled": all_met,
            "message": "ML activated" if all_met else "ML disabled: insufficient data",
            "thresholds": {
                "records": {"required": ML_MIN_RECORDS, "actual": total_records, "met": meets_records},
                "semesters": {"required": ML_MIN_SEMESTERS, "actual": total_exams, "met": meets_semesters},
                "positive_class": {"required": ML_MIN_POSITIVE_CLASS, "actual": positive_class, "met": meets_positive},
            },
            "note": (
                "Ground truth must be INDEPENDENT of rule-engine output to avoid circular validation. "
                "Default target: failed >= 1 subject in next semester. "
                "Temporal splitting only (never random). See docs/ml-methodology.md"
            ),
        }

    async def get_status(self) -> dict:
        return await self.check_activation_thresholds()
