"""Master data service — CRUD for all academic entities."""
from __future__ import annotations

import uuid
from typing import Any, Sequence

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.database.models import (
    Batch, Department, Examination, GradingScheme, Program,
    Section, Semester, Subject,
)


class DepartmentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_all(self) -> Sequence[Department]:
        r = await self._db.execute(select(Department).where(Department.is_deleted == False))
        return r.scalars().all()

    async def get(self, id: uuid.UUID) -> Department:
        r = await self._db.execute(
            select(Department).where(Department.id == id, Department.is_deleted == False)
        )
        dept = r.scalar_one_or_none()
        if not dept:
            raise NotFoundError("Department", id)
        return dept

    async def create(self, data: dict) -> Department:
        existing = await self._db.execute(
            select(Department).where(Department.code == data["code"])
        )
        if existing.scalar_one_or_none():
            raise AlreadyExistsError(f"Department with code '{data['code']}' already exists")
        dept = Department(**data)
        self._db.add(dept)
        await self._db.flush()
        return dept

    async def update(self, id: uuid.UUID, data: dict) -> Department:
        dept = await self.get(id)
        for k, v in data.items():
            if v is not None:
                setattr(dept, k, v)
        await self._db.flush()
        return dept

    async def delete(self, id: uuid.UUID) -> None:
        dept = await self.get(id)
        dept.is_deleted = True
        await self._db.flush()


class ProgramService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_all(self, department_id: uuid.UUID | None = None) -> Sequence[Program]:
        q = select(Program).where(Program.is_deleted == False)
        if department_id:
            q = q.where(Program.department_id == department_id)
        r = await self._db.execute(q)
        return r.scalars().all()

    async def get(self, id: uuid.UUID) -> Program:
        r = await self._db.execute(
            select(Program).where(Program.id == id, Program.is_deleted == False)
        )
        p = r.scalar_one_or_none()
        if not p:
            raise NotFoundError("Program", id)
        return p

    async def create(self, data: dict) -> Program:
        prog = Program(**data)
        self._db.add(prog)
        await self._db.flush()
        return prog

    async def update(self, id: uuid.UUID, data: dict) -> Program:
        prog = await self.get(id)
        for k, v in data.items():
            if v is not None:
                setattr(prog, k, v)
        await self._db.flush()
        return prog


class SubjectService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_all(self, department_id: uuid.UUID | None = None) -> Sequence[Subject]:
        q = select(Subject).where(Subject.is_deleted == False)
        if department_id:
            q = q.where(Subject.department_id == department_id)
        r = await self._db.execute(q)
        return r.scalars().all()

    async def get(self, id: uuid.UUID) -> Subject:
        r = await self._db.execute(
            select(Subject).where(Subject.id == id, Subject.is_deleted == False)
        )
        s = r.scalar_one_or_none()
        if not s:
            raise NotFoundError("Subject", id)
        return s

    async def get_by_code(self, code: str) -> Subject | None:
        r = await self._db.execute(
            select(Subject).where(Subject.code == code.upper(), Subject.is_deleted == False)
        )
        return r.scalar_one_or_none()

    async def create(self, data: dict) -> Subject:
        data["code"] = data["code"].upper()
        existing = await self.get_by_code(data["code"])
        if existing:
            raise AlreadyExistsError(f"Subject with code '{data['code']}' already exists")
        subj = Subject(**data)
        self._db.add(subj)
        await self._db.flush()
        return subj

    async def update(self, id: uuid.UUID, data: dict) -> Subject:
        subj = await self.get(id)
        for k, v in data.items():
            if v is not None:
                setattr(subj, k, v)
        await self._db.flush()
        return subj


class GradingSchemeService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_all(self) -> Sequence[GradingScheme]:
        r = await self._db.execute(select(GradingScheme).order_by(GradingScheme.effective_from.desc()))
        return r.scalars().all()

    async def get_active(self) -> GradingScheme | None:
        r = await self._db.execute(
            select(GradingScheme).where(GradingScheme.is_active == True).limit(1)
        )
        return r.scalar_one_or_none()

    async def get(self, id: uuid.UUID) -> GradingScheme:
        r = await self._db.execute(select(GradingScheme).where(GradingScheme.id == id))
        gs = r.scalar_one_or_none()
        if not gs:
            raise NotFoundError("GradingScheme", id)
        return gs

    async def create(self, data: dict) -> GradingScheme:
        gs = GradingScheme(**data)
        self._db.add(gs)
        await self._db.flush()
        return gs

    async def update(self, id: uuid.UUID, data: dict) -> GradingScheme:
        gs = await self.get(id)
        for k, v in data.items():
            if v is not None:
                setattr(gs, k, v)
        await self._db.flush()
        return gs
