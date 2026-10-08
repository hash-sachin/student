"""Evaluation runner — executes hypothesis checks."""
from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    AIGuardrailLog, AIInsight, AcademicAttentionScore,
    AuditLog, ExtractedRecordStaging, StudentSubjectResult,
    ValidationRecordStatus,
)

logger = structlog.get_logger(__name__)


class EvaluationRunner:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def run(self, hypothesis_id: str, config: dict) -> dict[str, Any]:
        handler = getattr(self, f"_run_{hypothesis_id.lower()}", None)
        if not handler:
            return {"passed": None, "error": f"No runner implemented for {hypothesis_id}"}
        return await handler(config)

    async def _run_h3(self, config: dict) -> dict:
        """H3: Analytics correctness — count of computed metrics."""
        r = await self._db.execute(select(func.count()).select_from(StudentSubjectResult))
        total_results = r.scalar_one()
        return {
            "hypothesis": "H3",
            "total_official_results": total_results,
            "note": "Full H3 validation requires reference spreadsheet comparison. "
                    "Run golden-file tests with pytest tests/evaluation/test_h3.py",
            "passed": None,
        }

    async def _run_h4(self, config: dict) -> dict:
        """H4: Attention scoring reproducibility."""
        r = await self._db.execute(select(func.count()).select_from(AcademicAttentionScore))
        total = r.scalar_one()
        return {
            "hypothesis": "H4",
            "total_scores": total,
            "note": "Reproducibility test: run identical inputs twice and compare hashes. "
                    "See tests/evaluation/test_h4_reproducibility.py",
            "passed": None,
        }

    async def _run_h6(self, config: dict) -> dict:
        """H6: AI grounding — numeric verification rate."""
        r = await self._db.execute(
            select(func.count()).select_from(AIInsight).where(AIInsight.guardrail_passed == True)
        )
        verified = r.scalar_one()
        r2 = await self._db.execute(select(func.count()).select_from(AIInsight))
        total = r2.scalar_one()

        verification_rate = (verified / total * 100) if total > 0 else None
        passed = verification_rate is not None and verification_rate >= 100.0 and total >= 50

        return {
            "hypothesis": "H6",
            "total_insights": total,
            "guardrail_passed_count": verified,
            "verification_rate_pct": round(verification_rate, 2) if verification_rate else None,
            "minimum_required": 50,
            "target_rate_pct": 100.0,
            "passed": passed,
        }

    async def _run_h7(self, config: dict) -> dict:
        """H7: Usability — requires manual faculty study."""
        return {
            "hypothesis": "H7",
            "note": "H7 requires a manual usability study with 2-3 faculty members. "
                    "Record findings in docs/evaluation/h7_usability_study.md",
            "required": ["task_success_rate", "clarity_rating", "sus_score >= 68"],
            "passed": None,
        }

    async def _run_h8(self, config: dict) -> dict:
        """H8: Performance — requires load test."""
        return {
            "hypothesis": "H8",
            "note": "H8 requires load testing with 1,000 students x 8 semesters. "
                    "Run: pytest tests/performance/test_h8_load.py",
            "target": "Dashboard p95 < 2s",
            "passed": None,
        }
