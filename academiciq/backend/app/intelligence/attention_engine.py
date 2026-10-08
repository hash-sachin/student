"""
AcademicAttention Engine v1.0
All outputs labeled ESTIMATED.
Factors: F1-F7. Configurable via scoring_configs table.
Reproducible: same inputs + same algorithm_version → same output.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    AcademicAttentionFactor, AcademicAttentionScore, AttentionBand,
    MetricLabel, ResultStatus, ScoringConfig, StudentSubjectResult,
)

logger = structlog.get_logger(__name__)

ALGORITHM_VERSION = "AcademicAttention-v1.0"
MIN_EVALUABLE_FACTORS = 2
MIN_CLASS_SIZE_FOR_F4 = 20  # F4 requires class n >= 20


# Default scoring config (stored in DB; this is the in-code reference default)
DEFAULT_SCORING_CONFIG = {
    "algorithm_version": ALGORITHM_VERSION,
    "weights": {
        "F1": {"thresholds": [5, 10, 15], "points": [0, 8, 14, 20], "max": 20},
        "F2": {"thresholds": [1, 2, 3], "points": [0, 8, 14, 20], "max": 20},
        "F3": {"points_per_subject": 8, "cap": 15, "max": 15},
        "F4": {"thresholds": [-0.5, -1.0, -1.5], "points": [0, 5, 10, 15], "max": 15},
        "F5": {"thresholds": [2, 3], "points": [0, 5, 10], "max": 10},
        "F6": {"thresholds": [60, 50, 40], "points": [0, 4, 7, 10], "max": 10},
        "F7": {"thresholds": [1, 2, 3], "points": [0, 0, 4, 10], "max": 10},
    },
    "thresholds": {
        "near_fail_margin": 10,
    },
    "band_definitions": {
        "NORMAL": [0, 24],
        "MONITOR": [25, 49],
        "ATTENTION": [50, 74],
        "HIGH_ATTENTION": [75, 100],
    },
}


@dataclass
class FactorResult:
    factor_id: str
    factor_name: str
    raw_value: str
    points: float
    max_points: float
    evidence: str
    skipped: bool = False
    skip_reason: str | None = None


@dataclass
class AttentionScoreResult:
    student_id: uuid.UUID
    examination_id: uuid.UUID
    raw_score: float
    band: AttentionBand
    factors: list[FactorResult]
    is_partial_score: bool
    missing_factors: list[str]
    algorithm_version: str
    scoring_config_id: uuid.UUID | None
    input_snapshot_hash: str
    metric_label: str = MetricLabel.ESTIMATED.value


class AttentionEngine:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def compute(
        self,
        student_id: uuid.UUID,
        examination_id: uuid.UUID,
        class_examination_id: uuid.UUID | None = None,
        section_id: uuid.UUID | None = None,
    ) -> AttentionScoreResult:
        """
        Compute attention score for a student in an examination.
        Reproducible: given same inputs + algorithm version, output is identical.
        """
        # Load scoring config
        config, config_id = await self._load_config()

        # Load current exam results
        current_results = await self._load_student_results(student_id, examination_id)

        # Load historical results (all prior exams for this student)
        historical = await self._load_historical_results(student_id, examination_id)

        # Load grading scheme
        from app.academics.service import GradingSchemeService
        gs = await GradingSchemeService(self._db).get_active()
        pass_mark = gs.pass_mark_overall if gs else 50

        # Compute semester average
        current_avg = self._compute_average(current_results)
        history_avgs = self._compute_history_averages(historical)

        # Build input snapshot for reproducibility
        snapshot_data = {
            "student_id": str(student_id),
            "examination_id": str(examination_id),
            "current_result_ids": sorted([str(r.id) for r in current_results]),
            "historical_result_ids": sorted([str(r.id) for h in historical.values() for r in h]),
            "algorithm_version": ALGORITHM_VERSION,
        }
        snapshot_hash = hashlib.sha256(
            json.dumps(snapshot_data, sort_keys=True).encode()
        ).hexdigest()

        # Compute factors
        factors: list[FactorResult] = []
        evaluable = 0
        missing: list[str] = []

        factors.append(self._f1_semester_decline(current_avg, history_avgs, config))
        factors.append(self._f2_failed_subjects(current_results, config))
        factors.append(self._f3_repeated_failure(current_results, historical, config))
        factors.append(await self._f4_class_relative(
            student_id, examination_id, section_id, current_avg, config
        ))
        factors.append(self._f5_continuous_decline(history_avgs, config))
        factors.append(self._f6_low_performance(current_avg, pass_mark, config))
        factors.append(self._f7_multiple_near_fail(current_results, pass_mark, config))

        for f in factors:
            if f.skipped:
                missing.append(f.factor_id)
            else:
                evaluable += 1

        is_partial = bool(missing)

        if evaluable < MIN_EVALUABLE_FACTORS:
            logger.warning(
                "attention_score_insufficient_factors",
                student_id=str(student_id),
                evaluable=evaluable,
            )
            # Return without score
            return AttentionScoreResult(
                student_id=student_id,
                examination_id=examination_id,
                raw_score=0.0,
                band=AttentionBand.NORMAL,
                factors=factors,
                is_partial_score=True,
                missing_factors=missing,
                algorithm_version=ALGORITHM_VERSION,
                scoring_config_id=config_id,
                input_snapshot_hash=snapshot_hash,
            )

        raw_score = sum(f.points for f in factors if not f.skipped)
        raw_score = min(raw_score, 100.0)
        band = self._score_to_band(raw_score, config)

        result = AttentionScoreResult(
            student_id=student_id,
            examination_id=examination_id,
            raw_score=round(raw_score, 2),
            band=band,
            factors=factors,
            is_partial_score=is_partial,
            missing_factors=missing,
            algorithm_version=ALGORITHM_VERSION,
            scoring_config_id=config_id,
            input_snapshot_hash=snapshot_hash,
        )

        # Persist
        await self._persist(result, config_id, config, snapshot_hash)
        return result

    # ------------------------------------------------------------------
    # Factor computations
    # ------------------------------------------------------------------

    def _f1_semester_decline(
        self,
        current_avg: float | None,
        history_avgs: list[float],
        config: dict,
    ) -> FactorResult:
        """F1: Semester average decline vs. previous semester."""
        if current_avg is None or not history_avgs:
            return FactorResult(
                "F1", "Semester Decline", "N/A", 0, 20,
                "No history", skipped=True,
                skip_reason="No previous semester average available"
            )
        prev = history_avgs[-1]
        drop = prev - current_avg
        w = config["weights"]["F1"]
        thresholds = w["thresholds"]  # [5, 10, 15]
        pts_list = w["points"]  # [0, 8, 14, 20]

        points = pts_list[0]
        for i, t in enumerate(thresholds):
            if drop >= t:
                points = pts_list[i + 1]

        evidence = f"Previous avg={prev:.2f} → Current avg={current_avg:.2f} (drop={drop:.2f})"
        return FactorResult("F1", "Semester Decline", f"{drop:.2f}", points, 20, evidence)

    def _f2_failed_subjects(
        self,
        current_results: list[StudentSubjectResult],
        config: dict,
    ) -> FactorResult:
        """F2: Number of failed subjects in current exam."""
        failed = sum(
            1 for r in current_results
            if r.result_status == ResultStatus.FAIL and not r.is_absent
        )
        w = config["weights"]["F2"]
        thresholds = w["thresholds"]  # [1, 2, 3]
        pts_list = w["points"]

        points = pts_list[0]
        for i, t in enumerate(thresholds):
            if failed >= t:
                points = pts_list[i + 1]

        return FactorResult("F2", "Failed Subjects (Current)", str(failed), points, 20,
                            f"Failed {failed} subject(s) this semester")

    def _f3_repeated_failure(
        self,
        current_results: list[StudentSubjectResult],
        historical: dict[uuid.UUID, list[StudentSubjectResult]],
        config: dict,
    ) -> FactorResult:
        """F3: Repeated failure in same subject across attempts."""
        if not historical:
            return FactorResult(
                "F3", "Repeated Failure", "N/A", 0, 15,
                "No history", skipped=True,
                skip_reason="No previous examination records"
            )
        w = config["weights"]["F3"]
        pps = w["points_per_subject"]
        cap = w["cap"]

        repeated: list[str] = []
        current_failed_subject_ids = {
            str(r.subject_id) for r in current_results
            if r.result_status == ResultStatus.FAIL
        }

        for exam_id, past_results in historical.items():
            for pr in past_results:
                if (pr.result_status == ResultStatus.FAIL and
                        str(pr.subject_id) in current_failed_subject_ids):
                    subj_key = str(pr.subject_id)
                    if subj_key not in repeated:
                        repeated.append(subj_key)

        points = min(len(repeated) * pps, cap)
        evidence = f"Failed in {len(repeated)} subject(s) across multiple attempts"
        return FactorResult("F3", "Repeated Failure", str(len(repeated)), points, 15, evidence)

    async def _f4_class_relative(
        self,
        student_id: uuid.UUID,
        examination_id: uuid.UUID,
        section_id: uuid.UUID | None,
        student_avg: float | None,
        config: dict,
    ) -> FactorResult:
        """F4: Class-relative deviation (Z-score). Requires class n >= 20."""
        if student_avg is None or section_id is None:
            return FactorResult(
                "F4", "Class-Relative Deviation", "N/A", 0, 15,
                "N/A", skipped=True,
                skip_reason="Insufficient data for class comparison"
            )

        # Get class averages
        from app.database.models import StudentSectionHistory
        r = await self._db.execute(
            select(StudentSectionHistory.student_id)
            .where(StudentSectionHistory.section_id == section_id)
        )
        class_student_ids = [row[0] for row in r.fetchall()]

        if len(class_student_ids) < MIN_CLASS_SIZE_FOR_F4:
            return FactorResult(
                "F4", "Class-Relative Deviation",
                f"Class n={len(class_student_ids)} (minimum {MIN_CLASS_SIZE_FOR_F4})",
                0, 15, "Insufficient class size",
                skipped=True,
                skip_reason=f"Class size {len(class_student_ids)} < minimum {MIN_CLASS_SIZE_FOR_F4}"
            )

        # Get all classmates' averages
        r2 = await self._db.execute(
            select(StudentSubjectResult)
            .where(
                StudentSubjectResult.student_id.in_(class_student_ids),
                StudentSubjectResult.examination_id == examination_id,
                StudentSubjectResult.is_latest_attempt == True,
            )
        )
        all_results = r2.scalars().all()

        student_marks: dict[uuid.UUID, list[float]] = {}
        for res in all_results:
            if not res.is_absent and res.total_marks is not None:
                student_marks.setdefault(res.student_id, []).append(float(res.total_marks))

        class_avgs = [float(np.mean(marks)) for marks in student_marks.values()]
        if len(class_avgs) < MIN_CLASS_SIZE_FOR_F4:
            return FactorResult(
                "F4", "Class-Relative Deviation", "N/A", 0, 15,
                "Insufficient class data", skipped=True,
                skip_reason="Insufficient class results for Z-score"
            )

        class_mean = float(np.mean(class_avgs))
        class_std = float(np.std(class_avgs))

        if class_std == 0:
            z = 0.0
        else:
            z = (student_avg - class_mean) / class_std

        w = config["weights"]["F4"]
        thresholds = w["thresholds"]  # [-0.5, -1.0, -1.5]
        pts_list = w["points"]        # [0, 5, 10, 15]

        points = pts_list[0]
        for i, t in enumerate(thresholds):
            if z <= t:
                points = pts_list[i + 1]

        evidence = (
            f"Student avg={student_avg:.2f}, Class mean={class_mean:.2f}, "
            f"Class SD={class_std:.2f}, Z-score={z:.2f}"
        )
        return FactorResult("F4", "Class-Relative Deviation", f"Z={z:.2f}", points, 15, evidence)

    def _f5_continuous_decline(
        self,
        history_avgs: list[float],
        config: dict,
    ) -> FactorResult:
        """F5: Continuous decline across consecutive semesters."""
        if len(history_avgs) < 2:
            return FactorResult(
                "F5", "Continuous Decline", "N/A", 0, 10,
                "Insufficient history", skipped=True,
                skip_reason="Need at least 2 prior semester averages"
            )

        consecutive = 1
        max_consecutive = 1
        for i in range(1, len(history_avgs)):
            if history_avgs[i] < history_avgs[i - 1]:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1

        w = config["weights"]["F5"]
        thresholds = w["thresholds"]  # [2, 3]
        pts_list = w["points"]        # [0, 5, 10]

        points = pts_list[0]
        for i, t in enumerate(thresholds):
            if max_consecutive >= t:
                points = pts_list[i + 1]

        evidence = f"Max consecutive declining semesters: {max_consecutive}"
        return FactorResult("F5", "Continuous Decline", str(max_consecutive), points, 10, evidence)

    def _f6_low_performance(
        self,
        current_avg: float | None,
        pass_mark: int,
        config: dict,
    ) -> FactorResult:
        """F6: Low current performance relative to pass mark."""
        if current_avg is None:
            return FactorResult(
                "F6", "Low Current Performance", "N/A", 0, 10,
                "No average", skipped=True,
                skip_reason="No current average available"
            )
        w = config["weights"]["F6"]
        thresholds = w["thresholds"]  # [60, 50, 40] (relative to pass mark 50)
        pts_list = w["points"]        # [0, 4, 7, 10]

        # Adjust thresholds relative to pass mark
        # Default thresholds assume pass_mark=50; scale accordingly
        scale = pass_mark / 50.0
        adjusted = [t * scale for t in thresholds]

        points = pts_list[0]
        for i, t in enumerate(sorted(adjusted, reverse=True)):
            if current_avg < t:
                points = pts_list[i + 1]

        evidence = f"Current average={current_avg:.2f} (pass mark={pass_mark})"
        return FactorResult("F6", "Low Current Performance", f"{current_avg:.2f}", points, 10, evidence)

    def _f7_multiple_near_fail(
        self,
        current_results: list[StudentSubjectResult],
        pass_mark: int,
        config: dict,
    ) -> FactorResult:
        """F7: Multiple subjects within near-fail margin of pass mark."""
        margin = config["thresholds"]["near_fail_margin"]
        near_fail = [
            r for r in current_results
            if not r.is_absent
            and r.total_marks is not None
            and pass_mark <= float(r.total_marks) <= pass_mark + margin
            and r.result_status == ResultStatus.PASS
        ]
        count = len(near_fail)

        w = config["weights"]["F7"]
        thresholds = w["thresholds"]  # [1, 2, 3]
        pts_list = w["points"]        # [0, 0, 4, 10]

        points = pts_list[0]
        for i, t in enumerate(thresholds):
            if count >= t:
                points = pts_list[i + 1]

        evidence = f"{count} subject(s) within {margin} marks of pass mark ({pass_mark})"
        return FactorResult("F7", "Multiple Near-Fail Subjects", str(count), points, 10, evidence)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _compute_average(self, results: list[StudentSubjectResult]) -> float | None:
        marks = [
            float(r.total_marks) for r in results
            if not r.is_absent and r.total_marks is not None
        ]
        return float(np.mean(marks)) if marks else None

    def _compute_history_averages(
        self,
        historical: dict[uuid.UUID, list[StudentSubjectResult]],
    ) -> list[float]:
        avgs: list[float] = []
        for results in historical.values():
            marks = [
                float(r.total_marks) for r in results
                if not r.is_absent and r.total_marks is not None
            ]
            if marks:
                avgs.append(float(np.mean(marks)))
        return avgs

    async def _load_student_results(
        self,
        student_id: uuid.UUID,
        examination_id: uuid.UUID,
    ) -> list[StudentSubjectResult]:
        r = await self._db.execute(
            select(StudentSubjectResult).where(
                StudentSubjectResult.student_id == student_id,
                StudentSubjectResult.examination_id == examination_id,
                StudentSubjectResult.is_latest_attempt == True,
            )
        )
        return list(r.scalars().all())

    async def _load_historical_results(
        self,
        student_id: uuid.UUID,
        current_examination_id: uuid.UUID,
    ) -> dict[uuid.UUID, list[StudentSubjectResult]]:
        """Load all prior exam results grouped by examination_id."""
        r = await self._db.execute(
            select(StudentSubjectResult).where(
                StudentSubjectResult.student_id == student_id,
                StudentSubjectResult.examination_id != current_examination_id,
                StudentSubjectResult.is_latest_attempt == True,
            )
        )
        results = r.scalars().all()
        grouped: dict[uuid.UUID, list[StudentSubjectResult]] = {}
        for res in results:
            grouped.setdefault(res.examination_id, []).append(res)
        return grouped

    async def _load_config(self) -> tuple[dict, uuid.UUID | None]:
        r = await self._db.execute(
            select(ScoringConfig).where(ScoringConfig.is_active == True).limit(1)
        )
        sc = r.scalar_one_or_none()
        if sc:
            return {
                "weights": sc.weights,
                "thresholds": sc.thresholds,
                "band_definitions": sc.band_definitions,
            }, sc.id
        return DEFAULT_SCORING_CONFIG, None

    def _score_to_band(self, score: float, config: dict) -> AttentionBand:
        bands = config["band_definitions"]
        for band_name, (lo, hi) in bands.items():
            if lo <= score <= hi:
                return AttentionBand[band_name]
        return AttentionBand.NORMAL

    async def _persist(
        self,
        result: AttentionScoreResult,
        config_id: uuid.UUID | None,
        config: dict,
        snapshot_hash: str,
    ) -> None:
        from datetime import datetime, timezone

        # Upsert score record
        existing = await self._db.execute(
            select(AcademicAttentionScore).where(
                AcademicAttentionScore.student_id == result.student_id,
                AcademicAttentionScore.examination_id == result.examination_id,
                AcademicAttentionScore.algorithm_version == ALGORITHM_VERSION,
            )
        )
        score_record = existing.scalar_one_or_none()

        if not score_record:
            score_record = AcademicAttentionScore(
                student_id=result.student_id,
                examination_id=result.examination_id,
                algorithm_version=ALGORITHM_VERSION,
                scoring_config_id=config_id,
                raw_score=result.raw_score,
                band=result.band,
                is_partial_score=result.is_partial_score,
                missing_factors=result.missing_factors,
                factor_values={f.factor_id: f.raw_value for f in result.factors},
                factor_points={f.factor_id: f.points for f in result.factors},
                input_snapshot_hash=snapshot_hash,
                calculation_timestamp=datetime.now(tz=timezone.utc),
            )
            self._db.add(score_record)
            await self._db.flush()

        # Persist individual factors
        for f in result.factors:
            self._db.add(AcademicAttentionFactor(
                score_id=score_record.id,
                factor_id=f.factor_id,
                factor_name=f.factor_name,
                raw_value=f.raw_value,
                points_awarded=f.points,
                max_points=f.max_points,
                evidence_description=f.evidence,
                skipped=f.skipped,
                skip_reason=f.skip_reason,
            ))

        await self._db.flush()
