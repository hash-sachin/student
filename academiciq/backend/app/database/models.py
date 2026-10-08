"""
AcademicIQ — All SQLAlchemy ORM models.
Table order: Identity & Access → Master Data → Document Intelligence →
             Results → Analytics → Attention → Evidence → Interventions →
             Simulation → AI → ML → Audit → Notifications → Evaluation
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, Float, ForeignKey,
    Integer, Numeric, SmallInteger, String, Text, UniqueConstraint,
    Index, func, CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

# Dialect-aware JSONB and UUID — work on both PostgreSQL and SQLite
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, SoftDeleteMixin, JSONB, UUID


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    HOD = "HOD"
    FACULTY = "FACULTY"
    STUDENT = "STUDENT"


class StudentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISCONTINUED = "DISCONTINUED"
    GRADUATED = "GRADUATED"
    ON_LEAVE = "ON_LEAVE"


class UploadProcessingStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    VALIDATION = "VALIDATION"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    COMMITTED = "COMMITTED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ValidationRecordStatus(str, enum.Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"
    UNMATCHED = "UNMATCHED"
    DUPLICATE = "DUPLICATE"
    SKIPPED = "SKIPPED"


class ExamType(str, enum.Enum):
    REGULAR = "REGULAR"
    SUPPLEMENTARY = "SUPPLEMENTARY"
    ARREAR = "ARREAR"
    REVALUATION = "REVALUATION"


class ResultStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ABSENT = "ABSENT"
    WITHHELD = "WITHHELD"
    MALPRACTICE = "MALPRACTICE"
    EXEMPTED = "EXEMPTED"
    PENDING = "PENDING"


class MetricLabel(str, enum.Enum):
    OFFICIAL = "OFFICIAL"
    CALCULATED = "CALCULATED"
    ESTIMATED = "ESTIMATED"
    HYPOTHETICAL = "HYPOTHETICAL"


class AttentionBand(str, enum.Enum):
    NORMAL = "NORMAL"
    MONITOR = "MONITOR"
    ATTENTION = "ATTENTION"
    HIGH_ATTENTION = "HIGH_ATTENTION"


class EvidenceNodeType(str, enum.Enum):
    INSIGHT = "INSIGHT"
    METRIC = "METRIC"
    CALCULATION = "CALCULATION"
    STUDENT = "STUDENT"
    SUBJECT = "SUBJECT"
    SEMESTER = "SEMESTER"
    EXAMINATION = "EXAMINATION"
    RESULT = "RESULT"
    SOURCE_UPLOAD = "SOURCE_UPLOAD"


class EvidenceEdgeType(str, enum.Enum):
    DERIVED_FROM = "DERIVED_FROM"
    COMPUTED_BY = "COMPUTED_BY"
    ABOUT = "ABOUT"
    OBSERVED_IN = "OBSERVED_IN"
    EXTRACTED_FROM = "EXTRACTED_FROM"


class InterventionStatus(str, enum.Enum):
    SUGGESTED = "SUGGESTED"
    APPROVED = "APPROVED"
    MODIFIED = "MODIFIED"
    DISMISSED = "DISMISSED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class RepeatedSubjectRule(str, enum.Enum):
    BEST = "BEST"
    LATEST = "LATEST"


# ---------------------------------------------------------------------------
# Identity & Access
# ---------------------------------------------------------------------------

class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    permissions: Mapped[list["Permission"]] = relationship(
        "Permission", secondary="role_permissions", back_populates="roles"
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="role")


class Permission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("resource", "action", "scope", name="uq_permission"),
    )

    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    scope: Mapped[str] = mapped_column(String(100), nullable=False, default="global")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        "Role", secondary="role_permissions", back_populates="permissions"
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    failed_login_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    department: Mapped["Department | None"] = relationship(
        "Department", foreign_keys=[department_id], back_populates="users"
    )


# ---------------------------------------------------------------------------
# Master Data
# ---------------------------------------------------------------------------

class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    head_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    programs: Mapped[list["Program"]] = relationship("Program", back_populates="department")
    users: Mapped[list["User"]] = relationship(
        "User", foreign_keys="User.department_id", back_populates="department"
    )
    head_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[head_user_id]
    )


class Program(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "programs"
    __table_args__ = (
        UniqueConstraint("code", "department_id", name="uq_program_code_dept"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )
    duration_semesters: Mapped[int] = mapped_column(SmallInteger, default=8, nullable=False)

    department: Mapped["Department"] = relationship("Department", back_populates="programs")
    batches: Mapped[list["Batch"]] = relationship("Batch", back_populates="program")


class Batch(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "batches"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id"), nullable=False, index=True
    )
    admission_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    program: Mapped["Program"] = relationship("Program", back_populates="batches")
    sections: Mapped[list["Section"]] = relationship("Section", back_populates="batch")


class Section(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "sections"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False, index=True
    )

    batch: Mapped["Batch"] = relationship("Batch", back_populates="sections")


class Subject(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "subjects"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3)
    max_internal_marks: Mapped[int] = mapped_column(SmallInteger, default=25, nullable=False)
    max_external_marks: Mapped[int] = mapped_column(SmallInteger, default=75, nullable=False)
    max_total_marks: Mapped[int] = mapped_column(SmallInteger, default=100, nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True
    )
    is_elective: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Semester(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "semesters"

    number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id"), nullable=False, index=True
    )


class Examination(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "examinations"

    semester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("semesters.id"), nullable=False, index=True
    )
    type: Mapped[ExamType] = mapped_column(
        Enum(ExamType, name="exam_type_enum"), nullable=False
    )
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    exam_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)

    semester: Mapped["Semester"] = relationship("Semester")


class SubjectOffering(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "subject_offerings"
    __table_args__ = (
        UniqueConstraint("subject_id", "semester_id", "section_id", name="uq_offering"),
    )

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False, index=True
    )
    semester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("semesters.id"), nullable=False, index=True
    )
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True, index=True
    )
    faculty_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )

    subject: Mapped["Subject"] = relationship("Subject")
    semester: Mapped["Semester"] = relationship("Semester")


class GradingScheme(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Versioned, effective-dated grading scheme. ADR-008."""
    __tablename__ = "grading_schemes"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    pass_mark_overall: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=50)
    pass_mark_internal: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    pass_mark_external: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # JSON: [{min, max, grade}] sorted descending by min
    grade_map: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    # JSON: {grade: grade_point}
    grade_point_map: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # JSON: formula or None
    gpa_formula: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # JSON: {code: description} e.g. {"AB": "Absent"}
    special_codes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # JSON: arrear policy details
    arrear_policy: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    repeated_subject_rule: Mapped[RepeatedSubjectRule] = mapped_column(
        Enum(RepeatedSubjectRule, name="repeated_subject_rule_enum"),
        nullable=False,
        default=RepeatedSubjectRule.LATEST,
    )
    credits_defined_in: Mapped[str] = mapped_column(
        String(30), nullable=False, default="SUBJECT_MASTER"
    )


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------

class Student(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "students"

    register_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    university_register_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id"), nullable=False, index=True
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False, index=True
    )
    admission_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[StudentStatus] = mapped_column(
        Enum(StudentStatus, name="student_status_enum"),
        nullable=False,
        default=StudentStatus.ACTIVE,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    department: Mapped["Department"] = relationship("Department")
    program: Mapped["Program"] = relationship("Program")
    batch: Mapped["Batch"] = relationship("Batch")
    section_history: Mapped[list["StudentSectionHistory"]] = relationship(
        "StudentSectionHistory", back_populates="student"
    )


class StudentSectionHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_section_history"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False, index=True
    )
    from_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    to_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="section_history")
    section: Mapped["Section"] = relationship("Section")


# ---------------------------------------------------------------------------
# Document Intelligence
# ---------------------------------------------------------------------------

class ResultUpload(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "result_uploads"

    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    semester_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("semesters.id"), nullable=True, index=True
    )
    examination_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("examinations.id"), nullable=True, index=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    processing_status: Mapped[UploadProcessingStatus] = mapped_column(
        Enum(UploadProcessingStatus, name="upload_processing_status_enum"),
        nullable=False,
        default=UploadProcessingStatus.QUEUED,
    )
    validation_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valid_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warning_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unmatched_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    parser_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    parser_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    parser_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    supersedes_upload_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("result_uploads.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hash_override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    processing_logs: Mapped[list["ResultProcessingLog"]] = relationship(
        "ResultProcessingLog", back_populates="upload"
    )
    staged_records: Mapped[list["ExtractedRecordStaging"]] = relationship(
        "ExtractedRecordStaging", back_populates="upload"
    )


class ResultProcessingLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "result_processing_logs"

    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("result_uploads.id"), nullable=False, index=True
    )
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    upload: Mapped["ResultUpload"] = relationship("ResultUpload", back_populates="processing_logs")


class ExtractedRecordStaging(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "extracted_records_staging"

    upload_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("result_uploads.id"), nullable=False, index=True
    )
    # Raw extracted values
    raw_register_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_subject_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_subject_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    raw_internal_marks: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_external_marks: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_total_marks: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    raw_result_status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Resolved references (nullable until validation)
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=True, index=True
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True, index=True
    )

    # Normalized numeric values
    internal_marks: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    external_marks: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_marks: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    result_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    special_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Provenance
    extraction_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bounding_box: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    line_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Validation
    validation_status: Mapped[ValidationRecordStatus] = mapped_column(
        Enum(ValidationRecordStatus, name="validation_record_status_enum"),
        nullable=False,
        default=ValidationRecordStatus.VALID,
    )
    validation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skip_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    upload: Mapped["ResultUpload"] = relationship("ResultUpload", back_populates="staged_records")


# ---------------------------------------------------------------------------
# Results (official, post-commit)
# ---------------------------------------------------------------------------

class StudentSubjectResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_subject_results"
    __table_args__ = (
        Index("ix_ssr_student_exam", "student_id", "examination_id"),
        Index("ix_ssr_subject_exam", "subject_id", "examination_id"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False, index=True
    )
    examination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("examinations.id"), nullable=False, index=True
    )
    upload_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("result_uploads.id"), nullable=True, index=True
    )
    grading_scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grading_schemes.id"), nullable=False, index=True
    )

    internal_marks: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    external_marks: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_marks: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    grade_point: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)

    result_status: Mapped[ResultStatus] = mapped_column(
        Enum(ResultStatus, name="result_status_enum"), nullable=False
    )
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    special_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    attempt_number: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    is_latest_attempt: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("student_subject_results.id"), nullable=True
    )

    # Provenance back to staging record
    staging_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extracted_records_staging.id"), nullable=True
    )


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class AcademicMetric(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Computed analytics values. All labeled CALCULATED."""
    __tablename__ = "academic_metrics"
    __table_args__ = (
        Index("ix_metric_student_exam", "student_id", "examination_id"),
    )

    student_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=True, index=True
    )
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True, index=True
    )
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True, index=True
    )
    examination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("examinations.id"), nullable=False, index=True
    )
    metric_type: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    metric_label: Mapped[MetricLabel] = mapped_column(
        Enum(MetricLabel, name="metric_label_enum"),
        nullable=False,
        default=MetricLabel.CALCULATED,
    )
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    grading_scheme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grading_schemes.id"), nullable=True
    )
    input_snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class AcademicTrend(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Detected trends (decline, improvement). All labeled CALCULATED."""
    __tablename__ = "academic_trends"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    from_examination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("examinations.id"), nullable=False
    )
    to_examination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("examinations.id"), nullable=False
    )
    trend_type: Mapped[str] = mapped_column(String(50), nullable=False)  # DECLINE, IMPROVEMENT, etc.
    direction: Mapped[str] = mapped_column(String(10), nullable=False)   # UP, DOWN
    magnitude: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True
    )
    evidence_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Academic Attention Engine
# ---------------------------------------------------------------------------

class ScoringConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Versioned attention algorithm configuration."""
    __tablename__ = "scoring_configs"

    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    weights: Mapped[dict] = mapped_column(JSONB, nullable=False)
    thresholds: Mapped[dict] = mapped_column(JSONB, nullable=False)
    band_definitions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class AcademicAttentionScore(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Per-student attention score. Label: ESTIMATED."""
    __tablename__ = "academic_attention_scores"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "examination_id", "algorithm_version",
            name="uq_attention_score"
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    examination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("examinations.id"), nullable=False, index=True
    )
    scoring_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scoring_configs.id"), nullable=False
    )
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    band: Mapped[AttentionBand] = mapped_column(
        Enum(AttentionBand, name="attention_band_enum"), nullable=False
    )
    is_partial_score: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    missing_factors: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    factor_values: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    factor_points: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    grading_scheme_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    upload_ids_used: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    input_snapshot_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    calculation_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    metric_label: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MetricLabel.ESTIMATED.value
    )

    factors: Mapped[list["AcademicAttentionFactor"]] = relationship(
        "AcademicAttentionFactor", back_populates="score"
    )


class AcademicAttentionFactor(Base, UUIDPrimaryKeyMixin):
    """Individual factor contribution to an attention score."""
    __tablename__ = "academic_attention_factors"

    score_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_attention_scores.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    factor_id: Mapped[str] = mapped_column(String(10), nullable=False)  # F1..F7
    factor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)  # human-readable
    points_awarded: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    max_points: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    evidence_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skip_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    score: Mapped["AcademicAttentionScore"] = relationship(
        "AcademicAttentionScore", back_populates="factors"
    )


# ---------------------------------------------------------------------------
# Evidence Graph
# ---------------------------------------------------------------------------

class EvidenceNode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidence_nodes"

    node_type: Mapped[EvidenceNodeType] = mapped_column(
        Enum(EvidenceNodeType, name="evidence_node_type_enum"), nullable=False, index=True
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class EvidenceEdge(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidence_edges"
    __table_args__ = (
        Index("ix_evidence_edge_from", "from_node_id"),
        Index("ix_evidence_edge_to", "to_node_id"),
    )

    from_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence_nodes.id", ondelete="CASCADE"), nullable=False
    )
    to_node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence_nodes.id", ondelete="CASCADE"), nullable=False
    )
    edge_type: Mapped[EvidenceEdgeType] = mapped_column(
        Enum(EvidenceEdgeType, name="evidence_edge_type_enum"), nullable=False
    )
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    from_node: Mapped["EvidenceNode"] = relationship(
        "EvidenceNode", foreign_keys=[from_node_id]
    )
    to_node: Mapped["EvidenceNode"] = relationship(
        "EvidenceNode", foreign_keys=[to_node_id]
    )


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------

class Intervention(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "interventions"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    examination_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("examinations.id"), nullable=True
    )
    rule_version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    trigger_evidence_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InterventionStatus] = mapped_column(
        Enum(InterventionStatus, name="intervention_status_enum"),
        nullable=False,
        default=InterventionStatus.SUGGESTED,
    )
    faculty_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    modified_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    actions: Mapped[list["InterventionAction"]] = relationship(
        "InterventionAction", back_populates="intervention"
    )


class InterventionAction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "intervention_actions"

    intervention_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interventions.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    performed_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome_examination_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("examinations.id"), nullable=True
    )
    outcome_delta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    intervention: Mapped["Intervention"] = relationship(
        "Intervention", back_populates="actions"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

class WhatIfScenario(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """What-if simulation scenarios. ALL outputs are HYPOTHETICAL."""
    __tablename__ = "what_if_scenarios"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    examination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("examinations.id"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    input_changes: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    baseline_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False)
    grading_scheme_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("grading_schemes.id"), nullable=True
    )
    # This flag is ALWAYS true — enforced at application layer
    is_hypothetical: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scenario_label: Mapped[str | None] = mapped_column(String(255), nullable=True)


# ---------------------------------------------------------------------------
# AI Insights
# ---------------------------------------------------------------------------

class AIInsight(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_insights"

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rendered_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    guardrail_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fallback_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    generated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )


class AIGuardrailLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_guardrail_logs"

    insight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_insights.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    check_type: Mapped[str] = mapped_column(String(50), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_number: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)


# ---------------------------------------------------------------------------
# ML Model Registry (optional layer)
# ---------------------------------------------------------------------------

class MLModelRegistry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ml_model_registry"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    training_data_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    temporal_split_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    feature_set: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    baseline_comparison: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


# ---------------------------------------------------------------------------
# Audit (append-only)
# ---------------------------------------------------------------------------

class AuditLog(Base, UUIDPrimaryKeyMixin):
    """
    Immutable append-only audit log.
    DB trigger or ORM event prevents UPDATE/DELETE on this table.
    """
    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class EvaluationRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evaluation_runs"

    hypothesis_id: Mapped[str] = mapped_column(String(10), nullable=False)  # H1..H8
    run_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    run_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
