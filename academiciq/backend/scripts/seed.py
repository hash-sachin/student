"""
AcademicIQ Database Seed Script.
Creates the demonstration scenario from Section 23 of the spec:
  - 60 students, 1 department, 1 program, 1 batch, 2 sections
  - 6 subjects, 8 semesters, 1 grading scheme
  - All roles and a default admin user
  - Synthetic result data with realistic distributions

Usage:
    cd backend && python scripts/seed.py

IMPORTANT: Clearly labeled SYNTHETIC DATA. Do NOT mix with real data.
"""
from __future__ import annotations

import asyncio
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import AsyncSessionLocal, async_engine
from app.database.base import Base
from app.database.models import (
    Batch, Department, Examination, ExamType, GradingScheme,
    Program, Role, Section, Semester, Subject, Student, StudentSectionHistory,
    User, UserRole, ScoringConfig, ResultStatus,
)
from app.core.security import hash_password
from app.intelligence.attention_engine import DEFAULT_SCORING_CONFIG

random.seed(42)

SYNTHETIC_MARKER = "[SYNTHETIC DATA - AcademicIQ Demo Seed]"

SUBJECT_DATA = [
    {"code": "MA101", "name": "Engineering Mathematics I", "credits": 4, "max_total_marks": 100},
    {"code": "PH101", "name": "Engineering Physics", "credits": 3, "max_total_marks": 100},
    {"code": "CH101", "name": "Engineering Chemistry", "credits": 3, "max_total_marks": 100},
    {"code": "CS101", "name": "Programming Fundamentals", "credits": 4, "max_total_marks": 100},
    {"code": "EE101", "name": "Basic Electrical Engineering", "credits": 3, "max_total_marks": 100},
    {"code": "ME101", "name": "Engineering Mechanics", "credits": 3, "max_total_marks": 100},
]

GRADE_MAP = [
    {"min": 91, "max": 100, "grade": "O"},
    {"min": 81, "max": 90, "grade": "A+"},
    {"min": 71, "max": 80, "grade": "A"},
    {"min": 61, "max": 70, "grade": "B+"},
    {"min": 50, "max": 60, "grade": "B"},
    {"min": 0, "max": 49, "grade": "F"},
]

GRADE_POINT_MAP = {"O": 10, "A+": 9, "A": 8, "B+": 7, "B": 6, "F": 0}


def random_marks(student_idx: int, subject_idx: int, semester: int, pattern: str) -> float:
    base = 65 + (student_idx % 3) * 5
    if pattern == "declining" and semester > 2:
        base -= (semester - 2) * 8
    elif pattern == "improving" and semester > 2:
        base += (semester - 2) * 5
    elif pattern == "struggling":
        base -= 20
    marks = base + random.gauss(0, 8)
    marks = max(0, min(100, marks))
    return round(marks, 1)


async def seed(db: AsyncSession) -> None:
    print(f"[SEED] Seeding AcademicIQ database... {SYNTHETIC_MARKER}")

    # --- Roles ---
    print("  Creating roles...")
    roles: dict[str, Role] = {}
    for role_name in UserRole:
        r = Role(name=role_name.value, description=f"{role_name.value} role")
        db.add(r)
        roles[role_name.value] = r
    await db.flush()

    # --- Users ---
    print("  Creating default users...")
    admin_user = User(
        email="admin@academiciq.edu",
        hashed_password=hash_password("Admin@123!"),
        full_name="System Administrator",
        role_id=roles[UserRole.ADMIN.value].id,
        is_active=True,
    )
    faculty_user = User(
        email="faculty@academiciq.edu",
        hashed_password=hash_password("Faculty@123!"),
        full_name="Dr. Faculty Member",
        role_id=roles[UserRole.FACULTY.value].id,
        is_active=True,
    )
    hod_user = User(
        email="hod@academiciq.edu",
        hashed_password=hash_password("Hod@123!"),
        full_name="Dr. HOD",
        role_id=roles[UserRole.HOD.value].id,
        is_active=True,
    )
    db.add_all([admin_user, faculty_user, hod_user])
    await db.flush()

    # --- Department ---
    print("  Creating academic structure...")
    dept = Department(name="Computer Science and Engineering", code="CSE")
    db.add(dept)
    await db.flush()

    admin_user.department_id = dept.id
    faculty_user.department_id = dept.id
    hod_user.department_id = dept.id
    dept.head_user_id = hod_user.id
    await db.flush()

    # --- Program ---
    program = Program(
        name="B.E. Computer Science and Engineering",
        code="BE-CSE",
        department_id=dept.id,
        duration_semesters=8,
    )
    db.add(program)
    await db.flush()

    # --- Batch + Sections ---
    batch = Batch(name="2022-2026", program_id=program.id, admission_year=2022)
    db.add(batch)
    await db.flush()

    section_a = Section(name="A", batch_id=batch.id)
    section_b = Section(name="B", batch_id=batch.id)
    db.add_all([section_a, section_b])
    await db.flush()

    # --- Grading Scheme ---
    print("  Creating grading scheme...")
    gs = GradingScheme(
        name="2021 Regulations",
        version="2021-R",
        effective_from=datetime(2021, 6, 1, tzinfo=timezone.utc),
        is_active=True,
        pass_mark_overall=50,
        grade_map=GRADE_MAP,
        grade_point_map=GRADE_POINT_MAP,
        gpa_formula={"type": "CREDIT_WEIGHTED", "credit_source": "SUBJECT_MASTER", "rounding": 2},
        special_codes={"AB": "Absent", "WH": "Withheld", "MP": "Malpractice"},
        arrear_policy={"count_in_analytics": True, "supplementary_affects_gpa": False},
        repeated_subject_rule="LATEST",
        credits_defined_in="SUBJECT_MASTER",
    )
    db.add(gs)
    await db.flush()

    # --- Scoring config ---
    sc = ScoringConfig(
        algorithm_version=DEFAULT_SCORING_CONFIG["algorithm_version"],
        weights=DEFAULT_SCORING_CONFIG["weights"],
        thresholds=DEFAULT_SCORING_CONFIG["thresholds"],
        band_definitions=DEFAULT_SCORING_CONFIG["band_definitions"],
        is_active=True,
        description="Default AcademicAttention-v1.0 configuration",
    )
    db.add(sc)
    await db.flush()

    # --- Subjects ---
    print("  Creating subjects...")
    subjects: list[Subject] = []
    for sd in SUBJECT_DATA:
        s = Subject(
            code=sd["code"],
            name=sd["name"],
            credits=sd["credits"],
            max_total_marks=sd["max_total_marks"],
            max_internal_marks=25,
            max_external_marks=75,
            department_id=dept.id,
        )
        db.add(s)
        subjects.append(s)
    await db.flush()

    # --- Semesters + Examinations ---
    print("  Creating semesters and examinations...")
    semesters: list[Semester] = []
    for sem_num in range(1, 9):
        sem = Semester(number=sem_num, name=f"Semester {sem_num}", program_id=program.id)
        db.add(sem)
        semesters.append(sem)
    await db.flush()

    examinations: list[Examination] = []
    for i, sem in enumerate(semesters[:4], start=1):
        exam = Examination(
            semester_id=sem.id,
            type=ExamType.REGULAR,
            academic_year=f"{2022 + (i - 1)//2}-{2023 + (i - 1)//2}",
            label=f"End Semester Examination - Semester {sem.number}",
        )
        db.add(exam)
        examinations.append(exam)
    await db.flush()

    # --- 60 Students ---
    print("  Creating 60 students...")
    students: list[Student] = []
    patterns = ["normal"] * 50 + ["declining"] * 5 + ["struggling"] * 3 + ["improving"] * 2

    for i in range(60):
        reg = f"22CSE{i + 1:03d}"
        student = Student(
            register_number=reg,
            university_register_number=f"U22CSE{i + 1:03d}",
            name=f"Student {i + 1:03d} {SYNTHETIC_MARKER}",
            department_id=dept.id,
            program_id=program.id,
            batch_id=batch.id,
            admission_year=2022,
            status="ACTIVE",
        )
        db.add(student)
        students.append(student)
    await db.flush()

    for i, student in enumerate(students):
        section = section_a if i < 30 else section_b
        history = StudentSectionHistory(
            student_id=student.id,
            section_id=section.id,
            from_date=datetime(2022, 6, 1, tzinfo=timezone.utc),
        )
        db.add(history)
    await db.flush()

    # --- Synthetic results ---
    print("  Creating synthetic results (4 semesters x 60 students x 6 subjects)...")
    from app.database.models import StudentSubjectResult

    def grade_from_marks(m: float) -> tuple[str, str, float]:
        for band in sorted(GRADE_MAP, key=lambda x: x["min"], reverse=True):
            if m >= band["min"]:
                grade = band["grade"]
                gp = GRADE_POINT_MAP.get(grade, 0)
                status = ResultStatus.PASS if grade != "F" else ResultStatus.FAIL
                return grade, status.value, gp
        return "F", ResultStatus.FAIL.value, 0

    for exam_idx, exam in enumerate(examinations):
        for s_idx, student in enumerate(students):
            pattern = patterns[s_idx]
            for sub_idx, subject in enumerate(subjects):
                marks = random_marks(s_idx, sub_idx, exam_idx + 1, pattern)
                grade, status, gp = grade_from_marks(marks)
                result = StudentSubjectResult(
                    student_id=student.id,
                    subject_id=subject.id,
                    examination_id=exam.id,
                    upload_id=None,
                    grading_scheme_id=gs.id,
                    internal_marks=round(marks * 0.25, 1),
                    external_marks=round(marks * 0.75, 1),
                    total_marks=marks,
                    grade=grade,
                    grade_point=gp,
                    result_status=status,
                    is_absent=False,
                    attempt_number=1,
                    is_latest_attempt=True,
                )
                db.add(result)

    await db.flush()
    print("  Synthetic results created.")

    # --- Student user accounts (first 5) ---
    print("  Creating student user accounts (first 5)...")
    for i, student in enumerate(students[:5]):
        u = User(
            email=f"student{i + 1}@academiciq.edu",
            hashed_password=hash_password("Student@123!"),
            full_name=f"Student {i + 1:03d}",
            role_id=roles[UserRole.STUDENT.value].id,
            department_id=dept.id,
            is_active=True,
        )
        db.add(u)
    await db.flush()

    await db.commit()
    print("")
    print("[SEED] Seed complete!")
    print("")
    print("Default credentials:")
    print("  Admin:   admin@academiciq.edu   / Admin@123!")
    print("  Faculty: faculty@academiciq.edu / Faculty@123!")
    print("  HOD:     hod@academiciq.edu     / Hod@123!")
    print("  Student: student1@academiciq.edu / Student@123!")
    print(f"\n{SYNTHETIC_MARKER}")


async def main() -> None:
    print("Creating database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
