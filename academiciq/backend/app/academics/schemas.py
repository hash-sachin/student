"""Pydantic schemas for master data: departments, programs, batches, sections,
subjects, semesters, examinations, grading schemes."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class UUIDSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


# ---------------------------------------------------------------------------
# Department
# ---------------------------------------------------------------------------

class DepartmentCreate(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=20)
    head_user_id: uuid.UUID | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    code: str | None = Field(None, max_length=20)
    head_user_id: uuid.UUID | None = None


class DepartmentRead(UUIDSchema):
    name: str
    code: str
    head_user_id: uuid.UUID | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Program
# ---------------------------------------------------------------------------

class ProgramCreate(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=20)
    department_id: uuid.UUID
    duration_semesters: int = Field(8, ge=1, le=12)


class ProgramUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    duration_semesters: int | None = None


class ProgramRead(UUIDSchema):
    name: str
    code: str
    department_id: uuid.UUID
    duration_semesters: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------

class BatchCreate(BaseModel):
    name: str = Field(..., max_length=100)
    program_id: uuid.UUID
    admission_year: int = Field(..., ge=2000, le=2100)


class BatchRead(UUIDSchema):
    name: str
    program_id: uuid.UUID
    admission_year: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Section
# ---------------------------------------------------------------------------

class SectionCreate(BaseModel):
    name: str = Field(..., max_length=50)
    batch_id: uuid.UUID


class SectionRead(UUIDSchema):
    name: str
    batch_id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------

class SubjectCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    credits: int = Field(3, ge=0, le=10)
    max_internal_marks: int = Field(25, ge=0)
    max_external_marks: int = Field(75, ge=0)
    max_total_marks: int = Field(100, ge=1)
    department_id: uuid.UUID | None = None
    is_elective: bool = False


class SubjectUpdate(BaseModel):
    name: str | None = None
    credits: int | None = None
    max_internal_marks: int | None = None
    max_external_marks: int | None = None
    max_total_marks: int | None = None
    is_elective: bool | None = None


class SubjectRead(UUIDSchema):
    code: str
    name: str
    credits: int
    max_internal_marks: int
    max_external_marks: int
    max_total_marks: int
    department_id: uuid.UUID | None
    is_elective: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Semester
# ---------------------------------------------------------------------------

class SemesterCreate(BaseModel):
    number: int = Field(..., ge=1, le=12)
    name: str = Field(..., max_length=100)
    program_id: uuid.UUID


class SemesterRead(UUIDSchema):
    number: int
    name: str
    program_id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Examination
# ---------------------------------------------------------------------------

class ExaminationCreate(BaseModel):
    semester_id: uuid.UUID
    type: str = Field(..., pattern="^(REGULAR|SUPPLEMENTARY|ARREAR|REVALUATION)$")
    academic_year: str = Field(..., max_length=20)
    exam_date: datetime | None = None
    label: str | None = Field(None, max_length=100)


class ExaminationRead(UUIDSchema):
    semester_id: uuid.UUID
    type: str
    academic_year: str
    exam_date: datetime | None
    label: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Grading Scheme
# ---------------------------------------------------------------------------

class GradingSchemeCreate(BaseModel):
    name: str = Field(..., max_length=100)
    version: str = Field(..., max_length=50)
    effective_from: datetime
    effective_to: datetime | None = None
    pass_mark_overall: int = Field(50, ge=0, le=100)
    pass_mark_internal: int | None = None
    pass_mark_external: int | None = None
    grade_map: list[dict[str, Any]] = Field(default_factory=list)
    grade_point_map: dict[str, float] = Field(default_factory=dict)
    gpa_formula: dict[str, Any] | None = None
    special_codes: dict[str, str] = Field(default_factory=dict)
    arrear_policy: dict[str, Any] = Field(default_factory=dict)
    repeated_subject_rule: str = Field("LATEST", pattern="^(BEST|LATEST)$")
    credits_defined_in: str = Field("SUBJECT_MASTER", pattern="^(SUBJECT_MASTER|SCHEME_TABLE)$")


class GradingSchemeRead(UUIDSchema):
    name: str
    version: str
    effective_from: datetime
    effective_to: datetime | None
    is_active: bool
    pass_mark_overall: int
    pass_mark_internal: int | None
    pass_mark_external: int | None
    grade_map: list[dict]
    grade_point_map: dict
    gpa_formula: dict | None
    special_codes: dict
    arrear_policy: dict
    repeated_subject_rule: str
    credits_defined_in: str
    created_at: datetime
