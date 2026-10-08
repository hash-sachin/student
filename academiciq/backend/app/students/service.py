"""Student service — CRUD + search."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.database.models import Student


class StudentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_students(
        self,
        page: int = 1,
        page_size: int = 20,
        department_id: uuid.UUID | None = None,
        program_id: uuid.UUID | None = None,
        batch_id: uuid.UUID | None = None,
        search: str | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[Student], int]:
        q = select(Student).where(Student.is_deleted == False)
        if department_id:
            q = q.where(Student.department_id == department_id)
        if program_id:
            q = q.where(Student.program_id == program_id)
        if batch_id:
            q = q.where(Student.batch_id == batch_id)
        if status:
            q = q.where(Student.status == status)
        if search:
            # Register number exact match is primary; name substring is secondary (suggested only)
            q = q.where(
                or_(
                    Student.register_number.ilike(f"%{search}%"),
                    Student.university_register_number.ilike(f"%{search}%"),
                )
            )

        count_q = select(func.count()).select_from(q.subquery())
        total_r = await self._db.execute(count_q)
        total = total_r.scalar_one()

        offset = (page - 1) * page_size
        q = q.order_by(Student.register_number).offset(offset).limit(page_size)
        r = await self._db.execute(q)
        return r.scalars().all(), total

    async def get(self, id: uuid.UUID) -> Student:
        r = await self._db.execute(
            select(Student).where(Student.id == id, Student.is_deleted == False)
        )
        s = r.scalar_one_or_none()
        if not s:
            raise NotFoundError("Student", id)
        return s

    async def get_by_register_number(self, register_number: str) -> Student | None:
        """Primary lookup by register number (the safe match key)."""
        r = await self._db.execute(
            select(Student).where(
                Student.register_number == register_number,
                Student.is_deleted == False,
            )
        )
        return r.scalar_one_or_none()

    async def find_by_name_similarity(self, name: str) -> list[Student]:
        """
        Name similarity search — returns SUGGESTED MATCHES ONLY.
        Must be flagged for human confirmation. Never auto-match.
        """
        r = await self._db.execute(
            select(Student).where(
                Student.name.ilike(f"%{name}%"),
                Student.is_deleted == False,
            ).limit(10)
        )
        return list(r.scalars().all())

    async def create(self, data: dict) -> Student:
        existing = await self.get_by_register_number(data["register_number"])
        if existing:
            raise AlreadyExistsError(
                f"Student with register number '{data['register_number']}' already exists"
            )
        student = Student(**data)
        self._db.add(student)
        await self._db.flush()
        return student

    async def update(self, id: uuid.UUID, data: dict) -> Student:
        student = await self.get(id)
        for k, v in data.items():
            if v is not None:
                setattr(student, k, v)
        await self._db.flush()
        return student

    async def bulk_create(self, records: list[dict]) -> tuple[list[Student], list[dict]]:
        """
        Bulk create students. Returns (created, errors).
        Register number uniqueness is enforced per-record.
        """
        created: list[Student] = []
        errors: list[dict] = []
        for rec in records:
            try:
                s = await self.create(rec)
                created.append(s)
            except AlreadyExistsError as e:
                errors.append({"register_number": rec.get("register_number"), "error": str(e)})
        return created, errors
