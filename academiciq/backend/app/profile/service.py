"""Longitudinal Academic Profile service."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analytics.engine import AnalyticsEngine
from app.core.exceptions import NotFoundError
from app.database.models import (
    AcademicAttentionScore, AcademicTrend, Examination,
    MetricLabel, ResultStatus, Semester, Student, StudentSubjectResult,
)
from app.intelligence.attention_engine import ALGORITHM_VERSION


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._analytics = AnalyticsEngine(db)

    async def get_longitudinal_profile(self, student_id: uuid.UUID) -> dict[str, Any]:
        """
        Assemble the full longitudinal academic profile.
        All metric values carry their metric_label (OFFICIAL / CALCULATED / ESTIMATED).
        """
        # Load student
        r = await self._db.execute(
            select(Student).where(Student.id == student_id, Student.is_deleted == False)
        )
        student = r.scalar_one_or_none()
        if not student:
            raise NotFoundError("Student", student_id)

        # Load all results for this student
        r2 = await self._db.execute(
            select(StudentSubjectResult)
            .where(
                StudentSubjectResult.student_id == student_id,
                StudentSubjectResult.is_latest_attempt == True,
            )
            .order_by(StudentSubjectResult.examination_id)
        )
        all_results = r2.scalars().all()

        # Group by examination
        by_exam: dict[uuid.UUID, list[StudentSubjectResult]] = {}
        for res in all_results:
            by_exam.setdefault(res.examination_id, []).append(res)

        # Load examinations
        exam_ids = list(by_exam.keys())
        r3 = await self._db.execute(
            select(Examination).where(Examination.id.in_(exam_ids))
        )
        exams: dict[uuid.UUID, Examination] = {e.id: e for e in r3.scalars().all()}

        # Build timeline entries
        timeline: list[dict] = []
        for exam_id in sorted(exam_ids, key=lambda eid: exams[eid].academic_year if eid in exams else ""):
            exam = exams.get(exam_id)
            results = by_exam[exam_id]
            exam_analytics = await self._analytics.compute_student_semester_analytics(student_id, exam_id)

            # Load attention score
            r4 = await self._db.execute(
                select(AcademicAttentionScore).where(
                    AcademicAttentionScore.student_id == student_id,
                    AcademicAttentionScore.examination_id == exam_id,
                    AcademicAttentionScore.algorithm_version == ALGORITHM_VERSION,
                )
            )
            att_score = r4.scalar_one_or_none()

            subject_results = []
            for res in results:
                subject_results.append({
                    "subject_id": str(res.subject_id),
                    "total_marks": float(res.total_marks) if res.total_marks else None,
                    "internal_marks": float(res.internal_marks) if res.internal_marks else None,
                    "external_marks": float(res.external_marks) if res.external_marks else None,
                    "grade": res.grade,
                    "grade_point": float(res.grade_point) if res.grade_point else None,
                    "result_status": res.result_status.value if res.result_status else None,
                    "is_absent": res.is_absent,
                    "attempt_number": res.attempt_number,
                    "metric_label": MetricLabel.OFFICIAL.value,
                })

            timeline.append({
                "examination_id": str(exam_id),
                "examination_type": exam.type.value if exam else None,
                "academic_year": exam.academic_year if exam else None,
                "subject_results": subject_results,
                "semester_metrics": {
                    "average": exam_analytics.semester_average,
                    "subjects_passed": exam_analytics.subjects_passed,
                    "subjects_failed": exam_analytics.subjects_failed,
                    "subjects_appeared": exam_analytics.subjects_appeared,
                    "metric_label": MetricLabel.CALCULATED.value,
                },
                "attention": {
                    "score": float(att_score.raw_score) if att_score else None,
                    "band": att_score.band.value if att_score else None,
                    "is_partial": att_score.is_partial_score if att_score else None,
                    "algorithm_version": ALGORITHM_VERSION,
                    "metric_label": MetricLabel.ESTIMATED.value,
                } if att_score else None,
            })

        # Load detected trends
        r5 = await self._db.execute(
            select(AcademicTrend).where(AcademicTrend.student_id == student_id)
        )
        trends = r5.scalars().all()

        declines = [t for t in trends if t.trend_type == "DECLINE"]
        improvements = [t for t in trends if t.trend_type == "IMPROVEMENT"]

        # Aggregate metrics
        all_marks = [
            float(r.total_marks)
            for results_list in by_exam.values()
            for r in results_list
            if not r.is_absent and r.total_marks is not None
        ]
        total_arrears = sum(
            1 for results_list in by_exam.values()
            for r in results_list
            if r.result_status == ResultStatus.FAIL
        )

        return {
            "student": {
                "id": str(student.id),
                "register_number": student.register_number,
                "name": student.name,
                "department_id": str(student.department_id),
                "program_id": str(student.program_id),
                "batch_id": str(student.batch_id),
                "status": student.status.value,
            },
            "profile_note": (
                "This is a Longitudinal Academic Profile — a structured representation of "
                "a student's academic history over time. "
                "'Academic Digital Twin' is a secondary alias (ADR-003)."
            ),
            "timeline": timeline,
            "aggregate_metrics": {
                "semesters_with_data": len(by_exam),
                "total_arrears": total_arrears,
                "overall_average": round(sum(all_marks) / len(all_marks), 4) if all_marks else None,
                "metric_label": MetricLabel.CALCULATED.value,
            },
            "detected_patterns": {
                "declines": [
                    {
                        "from_exam": str(d.from_examination_id),
                        "to_exam": str(d.to_examination_id),
                        "magnitude": float(d.magnitude),
                        "trend_type": d.trend_type,
                    }
                    for d in declines
                ],
                "improvements": [
                    {
                        "from_exam": str(i.from_examination_id),
                        "to_exam": str(i.to_examination_id),
                        "magnitude": float(i.magnitude),
                        "trend_type": i.trend_type,
                    }
                    for i in improvements
                ],
            },
        }
