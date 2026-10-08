"""
Validation Engine — validates extracted records against master data.
Produces staged records with statuses: VALID, WARNING, ERROR, UNMATCHED, DUPLICATE.
"""
from __future__ import annotations

import uuid
from typing import Sequence

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    ExtractedRecordStaging, GradingScheme, Student, Subject, ValidationRecordStatus
)
from app.parsers.base import ExtractedRecord

logger = structlog.get_logger(__name__)


class ValidationEngine:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def validate_and_stage(
        self,
        upload_id: uuid.UUID,
        records: list[ExtractedRecord],
    ) -> list[ExtractedRecordStaging]:
        """
        Validate all extracted records and persist them to staging table.
        Returns the list of staged records.
        """
        staged: list[ExtractedRecordStaging] = []
        seen_keys: set[tuple] = set()  # for duplicate detection within batch

        # Load active grading scheme for marks range validation
        gs = await self._get_active_grading_scheme()

        for rec in records:
            result = await self._validate_one(rec, upload_id, gs, seen_keys)
            staged.append(result)
            self._db.add(result)

        await self._db.flush()
        return staged

    async def _validate_one(
        self,
        rec: ExtractedRecord,
        upload_id: uuid.UUID,
        gs: GradingScheme | None,
        seen_keys: set,
    ) -> ExtractedRecordStaging:
        errors: list[str] = []
        warnings: list[str] = []
        final_status = ValidationRecordStatus.VALID

        # ----------------------------------------------------------------
        # 1. Register number lookup (primary safe match key)
        # ----------------------------------------------------------------
        student_id: uuid.UUID | None = None
        if rec.raw_register_number:
            r = await self._db.execute(
                select(Student).where(
                    Student.register_number == rec.raw_register_number.strip(),
                    Student.is_deleted == False,
                )
            )
            student = r.scalar_one_or_none()
            if student:
                student_id = student.id
            else:
                final_status = ValidationRecordStatus.UNMATCHED
                warnings.append(
                    f"Register number '{rec.raw_register_number}' not found in student master"
                )
        else:
            final_status = ValidationRecordStatus.ERROR
            errors.append("Missing register number")

        # ----------------------------------------------------------------
        # 2. Subject code lookup
        # ----------------------------------------------------------------
        subject_id: uuid.UUID | None = None
        if rec.raw_subject_code:
            r2 = await self._db.execute(
                select(Subject).where(
                    Subject.code == rec.raw_subject_code.strip().upper(),
                    Subject.is_deleted == False,
                )
            )
            subject = r2.scalar_one_or_none()
            if subject:
                subject_id = subject.id
            else:
                if final_status == ValidationRecordStatus.VALID:
                    final_status = ValidationRecordStatus.WARNING
                warnings.append(f"Subject code '{rec.raw_subject_code}' not found in subject master")

        # ----------------------------------------------------------------
        # 3. Marks range validation
        # ----------------------------------------------------------------
        int_val, int_absent = self._parse_marks(rec.raw_internal_marks)
        ext_val, ext_absent = self._parse_marks(rec.raw_external_marks)
        tot_val, tot_absent = self._parse_marks(rec.raw_total_marks)

        if subject_id and tot_val is not None:
            r3 = await self._db.execute(select(Subject).where(Subject.id == subject_id))
            subj = r3.scalar_one_or_none()
            if subj and tot_val > subj.max_total_marks:
                final_status = ValidationRecordStatus.ERROR
                errors.append(
                    f"Total marks {tot_val} exceeds maximum {subj.max_total_marks}"
                )
            if subj and int_val is not None and int_val > subj.max_internal_marks:
                warnings.append(
                    f"Internal marks {int_val} exceeds maximum {subj.max_internal_marks}"
                )

        # ----------------------------------------------------------------
        # 4. Grade consistency check (if grading scheme loaded)
        # ----------------------------------------------------------------
        if gs and tot_val is not None and rec.raw_grade:
            expected_grade = self._compute_grade(tot_val, gs)
            if expected_grade and expected_grade != rec.raw_grade.strip().upper():
                if final_status == ValidationRecordStatus.VALID:
                    final_status = ValidationRecordStatus.WARNING
                warnings.append(
                    f"Grade '{rec.raw_grade}' inconsistent with marks {tot_val} "
                    f"(expected '{expected_grade}')"
                )

        # ----------------------------------------------------------------
        # 5. Duplicate detection within this batch
        # ----------------------------------------------------------------
        dup_key = (rec.raw_register_number, rec.raw_subject_code)
        if dup_key in seen_keys:
            final_status = ValidationRecordStatus.DUPLICATE
            warnings.append(
                f"Duplicate record for register={rec.raw_register_number}, "
                f"subject={rec.raw_subject_code}"
            )
        else:
            seen_keys.add(dup_key)

        # ----------------------------------------------------------------
        # 6. Low-confidence OCR flag
        # ----------------------------------------------------------------
        if rec.confidence_score < 0.6 and final_status == ValidationRecordStatus.VALID:
            final_status = ValidationRecordStatus.WARNING
            warnings.append(f"Low extraction confidence ({rec.confidence_score:.2f}) — review required")

        # ----------------------------------------------------------------
        # Assemble staged record
        # ----------------------------------------------------------------
        note_parts: list[str] = []
        if warnings:
            note_parts.append("WARNINGS: " + "; ".join(warnings))
        if errors:
            note_parts.append("ERRORS: " + "; ".join(errors))

        return ExtractedRecordStaging(
            upload_id=upload_id,
            raw_register_number=rec.raw_register_number,
            raw_subject_code=rec.raw_subject_code,
            raw_subject_name=rec.raw_subject_name,
            raw_internal_marks=rec.raw_internal_marks,
            raw_external_marks=rec.raw_external_marks,
            raw_total_marks=rec.raw_total_marks,
            raw_grade=rec.raw_grade,
            raw_result_status=rec.raw_result_status,
            student_id=student_id,
            subject_id=subject_id,
            internal_marks=int_val,
            external_marks=ext_val,
            total_marks=tot_val,
            grade=self._parse_grade(rec.raw_grade),
            result_status=self._parse_result_status(rec.raw_result_status),
            is_absent=rec.is_absent or (int_absent and ext_absent),
            special_code=rec.special_code,
            extraction_method=rec.extraction_method,
            confidence_score=rec.confidence_score,
            page_number=rec.page_number,
            bounding_box=rec.bounding_box,
            line_reference=rec.line_reference,
            validation_status=final_status,
            validation_notes="\n".join(note_parts) or None,
            error_reason="; ".join(errors) if errors else None,
        )

    def _parse_marks(self, raw: str | None) -> tuple[float | None, bool]:
        if raw is None:
            return None, False
        stripped = raw.strip().upper()
        if stripped in ("AB", "ABS", "ABSENT", "-", "--", "A"):
            return None, True
        try:
            return float(stripped), False
        except ValueError:
            return None, False

    def _parse_grade(self, raw: str | None) -> str | None:
        return raw.strip().upper() if raw else None

    def _parse_result_status(self, raw: str | None) -> str | None:
        if not raw:
            return None
        mapping = {
            "P": "PASS", "PASS": "PASS",
            "F": "FAIL", "FAIL": "FAIL",
            "W": "WITHHELD", "WH": "WITHHELD",
            "AB": "ABSENT", "ABS": "ABSENT",
        }
        return mapping.get(raw.strip().upper(), raw.strip().upper())

    def _compute_grade(self, marks: float, gs: GradingScheme) -> str | None:
        grade_map = gs.grade_map
        if not grade_map:
            return None
        for band in sorted(grade_map, key=lambda x: x.get("min", 0), reverse=True):
            if marks >= band.get("min", 0):
                return band.get("grade")
        return None

    async def _get_active_grading_scheme(self) -> GradingScheme | None:
        r = await self._db.execute(
            select(GradingScheme).where(GradingScheme.is_active == True).limit(1)
        )
        return r.scalar_one_or_none()
