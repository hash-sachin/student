"""
Analytics Engine — Layer 1 Deterministic Analytics.
ALL outputs labeled CALCULATED. Reproducible. No ML, no AI.
Covers: student, subject, class, semester, department analytics.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    AcademicMetric, MetricLabel, Student, StudentSubjectResult,
    Subject, ResultStatus,
)

logger = structlog.get_logger(__name__)

ALGORITHM_VERSION = "1.0"
MIN_CLASS_SIZE_FOR_COMPARISON = 20  # Section 15: comparison only when n >= 20


def _snapshot_hash(data: Any) -> str:
    """SHA-256 hash of input data for reproducibility tracking."""
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class SubjectAnalytics:
    subject_id: uuid.UUID
    subject_code: str
    subject_name: str
    examination_id: uuid.UUID

    # OFFICIAL values
    marks: list[float] = field(default_factory=list)

    # CALCULATED values
    total_appeared: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_absent: int = 0
    pass_percentage: float = 0.0
    fail_percentage: float = 0.0
    average: float | None = None
    median: float | None = None
    minimum: float | None = None
    maximum: float | None = None
    std_dev: float | None = None
    grade_distribution: dict[str, int] = field(default_factory=dict)

    metric_label: str = MetricLabel.CALCULATED.value
    algorithm_version: str = ALGORITHM_VERSION
    input_snapshot_hash: str = ""


@dataclass
class StudentSemesterAnalytics:
    student_id: uuid.UUID
    examination_id: uuid.UUID

    # OFFICIAL from source
    subject_results: list[dict] = field(default_factory=list)

    # CALCULATED
    semester_average: float | None = None
    subjects_passed: int = 0
    subjects_failed: int = 0
    subjects_appeared: int = 0
    subjects_absent: int = 0
    gpa: float | None = None  # only if grading scheme defines formula

    metric_label: str = MetricLabel.CALCULATED.value
    algorithm_version: str = ALGORITHM_VERSION
    input_snapshot_hash: str = ""


class AnalyticsEngine:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Student Analytics
    # ------------------------------------------------------------------

    async def compute_student_semester_analytics(
        self,
        student_id: uuid.UUID,
        examination_id: uuid.UUID,
    ) -> StudentSemesterAnalytics:
        """Compute analytics for a single student in a single examination."""
        r = await self._db.execute(
            select(StudentSubjectResult)
            .where(
                StudentSubjectResult.student_id == student_id,
                StudentSubjectResult.examination_id == examination_id,
                StudentSubjectResult.is_latest_attempt == True,
            )
        )
        results = r.scalars().all()

        if not results:
            return StudentSemesterAnalytics(
                student_id=student_id,
                examination_id=examination_id,
            )

        marks_list: list[float] = []
        passed = failed = absent = appeared = 0
        subject_results: list[dict] = []

        for res in results:
            appeared += 1
            if res.is_absent or res.result_status == ResultStatus.ABSENT:
                absent += 1
                subject_results.append({
                    "subject_id": str(res.subject_id),
                    "total_marks": None,
                    "grade": res.grade,
                    "result_status": ResultStatus.ABSENT.value,
                    "is_absent": True,
                    "metric_label": MetricLabel.OFFICIAL.value,
                })
                continue

            if res.total_marks is not None:
                marks_list.append(float(res.total_marks))

            status = res.result_status.value if res.result_status else "PENDING"
            if status == ResultStatus.PASS.value:
                passed += 1
            elif status == ResultStatus.FAIL.value:
                failed += 1

            subject_results.append({
                "subject_id": str(res.subject_id),
                "total_marks": float(res.total_marks) if res.total_marks else None,
                "internal_marks": float(res.internal_marks) if res.internal_marks else None,
                "external_marks": float(res.external_marks) if res.external_marks else None,
                "grade": res.grade,
                "grade_point": float(res.grade_point) if res.grade_point else None,
                "result_status": status,
                "is_absent": False,
                "metric_label": MetricLabel.OFFICIAL.value,
            })

        avg = float(np.mean(marks_list)) if marks_list else None
        snapshot = _snapshot_hash(
            {"student_id": str(student_id), "examination_id": str(examination_id),
             "results": [str(r.id) for r in results]}
        )

        analytics = StudentSemesterAnalytics(
            student_id=student_id,
            examination_id=examination_id,
            subject_results=subject_results,
            semester_average=round(avg, 4) if avg is not None else None,
            subjects_passed=passed,
            subjects_failed=failed,
            subjects_appeared=appeared,
            subjects_absent=absent,
            input_snapshot_hash=snapshot,
        )

        # Persist metrics
        await self._persist_student_metric(
            student_id, examination_id, "semester_average", analytics.semester_average, snapshot
        )
        await self._persist_student_metric(
            student_id, examination_id, "subjects_failed", float(failed), snapshot
        )
        await self._persist_student_metric(
            student_id, examination_id, "subjects_passed", float(passed), snapshot
        )
        await self._db.flush()

        return analytics

    # ------------------------------------------------------------------
    # Subject Analytics
    # ------------------------------------------------------------------

    async def compute_subject_analytics(
        self,
        subject_id: uuid.UUID,
        examination_id: uuid.UUID,
    ) -> SubjectAnalytics:
        """Compute analytics for one subject in one examination."""
        r_subj = await self._db.execute(
            select(Subject).where(Subject.id == subject_id)
        )
        subject = r_subj.scalar_one_or_none()

        r = await self._db.execute(
            select(StudentSubjectResult)
            .where(
                StudentSubjectResult.subject_id == subject_id,
                StudentSubjectResult.examination_id == examination_id,
                StudentSubjectResult.is_latest_attempt == True,
            )
        )
        results = r.scalars().all()

        marks: list[float] = []
        passed = failed = absent = appeared = 0
        grade_dist: dict[str, int] = {}

        for res in results:
            appeared += 1
            if res.is_absent or res.result_status == ResultStatus.ABSENT:
                absent += 1
                continue
            status = res.result_status.value if res.result_status else "PENDING"
            if status == ResultStatus.PASS.value:
                passed += 1
            elif status == ResultStatus.FAIL.value:
                failed += 1
            if res.total_marks is not None:
                marks.append(float(res.total_marks))
            if res.grade:
                grade_dist[res.grade] = grade_dist.get(res.grade, 0) + 1

        appeared_non_absent = appeared - absent
        pass_pct = (passed / appeared_non_absent * 100) if appeared_non_absent > 0 else 0.0
        fail_pct = (failed / appeared_non_absent * 100) if appeared_non_absent > 0 else 0.0

        snapshot = _snapshot_hash(
            {"subject_id": str(subject_id), "examination_id": str(examination_id),
             "results": [str(r.id) for r in results]}
        )

        sa = SubjectAnalytics(
            subject_id=subject_id,
            subject_code=subject.code if subject else "",
            subject_name=subject.name if subject else "",
            examination_id=examination_id,
            marks=marks,
            total_appeared=appeared,
            total_passed=passed,
            total_failed=failed,
            total_absent=absent,
            pass_percentage=round(pass_pct, 2),
            fail_percentage=round(fail_pct, 2),
            average=round(float(np.mean(marks)), 4) if marks else None,
            median=round(float(np.median(marks)), 4) if marks else None,
            minimum=round(float(np.min(marks)), 4) if marks else None,
            maximum=round(float(np.max(marks)), 4) if marks else None,
            std_dev=round(float(np.std(marks)), 4) if marks else None,
            grade_distribution=grade_dist,
            input_snapshot_hash=snapshot,
        )

        await self._persist_subject_metrics(sa, examination_id, snapshot)
        await self._db.flush()
        return sa

    # ------------------------------------------------------------------
    # Class Analytics
    # ------------------------------------------------------------------

    async def compute_class_analytics(
        self,
        section_id: uuid.UUID,
        examination_id: uuid.UUID,
    ) -> dict:
        """
        Compute class-level analytics. Section comparison only when n >= 20.
        Label: CALCULATED.
        """
        from app.database.models import StudentSectionHistory
        r = await self._db.execute(
            select(StudentSectionHistory.student_id)
            .where(StudentSectionHistory.section_id == section_id)
        )
        student_ids = [row[0] for row in r.fetchall()]
        n = len(student_ids)

        if n == 0:
            return {"section_id": str(section_id), "n": 0, "error": "No students in section"}

        # Gather all results for these students in this examination
        r2 = await self._db.execute(
            select(StudentSubjectResult)
            .where(
                StudentSubjectResult.student_id.in_(student_ids),
                StudentSubjectResult.examination_id == examination_id,
                StudentSubjectResult.is_latest_attempt == True,
            )
        )
        results = r2.scalars().all()

        averages: list[float] = []
        failed_students: set[uuid.UUID] = set()

        for res in results:
            if res.result_status == ResultStatus.FAIL:
                failed_students.add(res.student_id)

        # Compute per-student averages
        student_marks: dict[uuid.UUID, list[float]] = {}
        for res in results:
            if not res.is_absent and res.total_marks is not None:
                student_marks.setdefault(res.student_id, []).append(float(res.total_marks))

        for marks in student_marks.values():
            averages.append(float(np.mean(marks)))

        result = {
            "section_id": str(section_id),
            "examination_id": str(examination_id),
            "metric_label": MetricLabel.CALCULATED.value,
            "algorithm_version": ALGORITHM_VERSION,
            "n": n,
            "class_average": round(float(np.mean(averages)), 4) if averages else None,
            "class_median": round(float(np.median(averages)), 4) if averages else None,
            "class_std_dev": round(float(np.std(averages)), 4) if averages else None,
            "class_min": round(float(np.min(averages)), 4) if averages else None,
            "class_max": round(float(np.max(averages)), 4) if averages else None,
            "pass_count": n - len(failed_students),
            "fail_count": len(failed_students),
            "pass_percentage": round((n - len(failed_students)) / n * 100, 2) if n else 0,
        }

        if n < MIN_CLASS_SIZE_FOR_COMPARISON:
            result["comparison_note"] = (
                f"Sample too small for reliable comparison (n={n}, minimum={MIN_CLASS_SIZE_FOR_COMPARISON})"
            )

        return result

    # ------------------------------------------------------------------
    # Semester comparison
    # ------------------------------------------------------------------

    async def compute_semester_comparison(
        self,
        student_id: uuid.UUID,
        exam_id_from: uuid.UUID,
        exam_id_to: uuid.UUID,
    ) -> dict:
        """Compare a student's performance between two examinations."""
        analytics_from = await self.compute_student_semester_analytics(student_id, exam_id_from)
        analytics_to = await self.compute_student_semester_analytics(student_id, exam_id_to)

        avg_from = analytics_from.semester_average
        avg_to = analytics_to.semester_average

        delta: float | None = None
        pct_change: float | None = None
        direction: str | None = None

        if avg_from is not None and avg_to is not None:
            delta = round(avg_to - avg_from, 4)
            if avg_from > 0:
                pct_change = round((delta / avg_from) * 100, 2)
            direction = "IMPROVEMENT" if delta > 0 else ("DECLINE" if delta < 0 else "STABLE")

        return {
            "student_id": str(student_id),
            "from_examination_id": str(exam_id_from),
            "to_examination_id": str(exam_id_to),
            "average_from": avg_from,
            "average_to": avg_to,
            "delta": delta,
            "percentage_change": pct_change,
            "direction": direction,
            "failed_from": analytics_from.subjects_failed,
            "failed_to": analytics_to.subjects_failed,
            "metric_label": MetricLabel.CALCULATED.value,
            "algorithm_version": ALGORITHM_VERSION,
        }

    # ------------------------------------------------------------------
    # Helper: persist metrics
    # ------------------------------------------------------------------

    async def _persist_student_metric(
        self,
        student_id: uuid.UUID,
        examination_id: uuid.UUID,
        metric_type: str,
        value: float | None,
        snapshot: str,
    ) -> None:
        existing = await self._db.execute(
            select(AcademicMetric).where(
                AcademicMetric.student_id == student_id,
                AcademicMetric.examination_id == examination_id,
                AcademicMetric.metric_type == metric_type,
                AcademicMetric.algorithm_version == ALGORITHM_VERSION,
            )
        )
        m = existing.scalar_one_or_none()
        if m:
            m.metric_value = value
            m.input_snapshot_hash = snapshot
        else:
            self._db.add(AcademicMetric(
                student_id=student_id,
                examination_id=examination_id,
                metric_type=metric_type,
                metric_value=value,
                metric_label=MetricLabel.CALCULATED,
                algorithm_version=ALGORITHM_VERSION,
                input_snapshot_hash=snapshot,
            ))

    async def _persist_subject_metrics(
        self,
        sa: SubjectAnalytics,
        examination_id: uuid.UUID,
        snapshot: str,
    ) -> None:
        metrics = [
            ("subject_average", sa.average),
            ("subject_pass_percentage", sa.pass_percentage),
            ("subject_fail_percentage", sa.fail_percentage),
            ("subject_median", sa.median),
            ("subject_std_dev", sa.std_dev),
        ]
        for metric_type, value in metrics:
            existing = await self._db.execute(
                select(AcademicMetric).where(
                    AcademicMetric.subject_id == sa.subject_id,
                    AcademicMetric.examination_id == examination_id,
                    AcademicMetric.metric_type == metric_type,
                )
            )
            m = existing.scalar_one_or_none()
            if m:
                m.metric_value = value
            else:
                self._db.add(AcademicMetric(
                    subject_id=sa.subject_id,
                    examination_id=examination_id,
                    metric_type=metric_type,
                    metric_value=value,
                    metric_label=MetricLabel.CALCULATED,
                    algorithm_version=ALGORITHM_VERSION,
                    input_snapshot_hash=snapshot,
                ))
