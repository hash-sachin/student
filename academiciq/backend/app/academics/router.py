"""Master data API routers."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.academics.schemas import (
    DepartmentCreate, DepartmentRead, DepartmentUpdate,
    ProgramCreate, ProgramRead, ProgramUpdate,
    SubjectCreate, SubjectRead, SubjectUpdate,
    GradingSchemeCreate, GradingSchemeRead,
    BatchCreate, BatchRead, SectionCreate, SectionRead,
    SemesterCreate, SemesterRead, ExaminationCreate, ExaminationRead,
)
from app.academics.service import DepartmentService, ProgramService, SubjectService, GradingSchemeService
from app.auth.dependencies import CurrentUser
from app.database.models import Batch, Examination, Section, Semester
from app.database.session import get_db

router = APIRouter(tags=["master-data"])


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------

@router.get("/departments", response_model=list[DepartmentRead])
async def list_departments(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = DepartmentService(db)
    return await svc.list_all()


@router.post("/departments", response_model=DepartmentRead, status_code=201)
async def create_department(
    body: DepartmentCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = DepartmentService(db)
    return await svc.create(body.model_dump())


@router.get("/departments/{id}", response_model=DepartmentRead)
async def get_department(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = DepartmentService(db)
    return await svc.get(id)


@router.put("/departments/{id}", response_model=DepartmentRead)
async def update_department(
    id: uuid.UUID,
    body: DepartmentUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = DepartmentService(db)
    return await svc.update(id, body.model_dump(exclude_none=True))


# ---------------------------------------------------------------------------
# Programs
# ---------------------------------------------------------------------------

@router.get("/programs", response_model=list[ProgramRead])
async def list_programs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    department_id: uuid.UUID | None = None,
):
    svc = ProgramService(db)
    return await svc.list_all(department_id=department_id)


@router.post("/programs", response_model=ProgramRead, status_code=201)
async def create_program(
    body: ProgramCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ProgramService(db)
    return await svc.create(body.model_dump())


@router.get("/programs/{id}", response_model=ProgramRead)
async def get_program(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = ProgramService(db)
    return await svc.get(id)


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

@router.get("/subjects", response_model=list[SubjectRead])
async def list_subjects(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    department_id: uuid.UUID | None = None,
):
    svc = SubjectService(db)
    return await svc.list_all(department_id=department_id)


@router.post("/subjects", response_model=SubjectRead, status_code=201)
async def create_subject(
    body: SubjectCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = SubjectService(db)
    return await svc.create(body.model_dump())


@router.get("/subjects/{id}", response_model=SubjectRead)
async def get_subject(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = SubjectService(db)
    return await svc.get(id)


@router.put("/subjects/{id}", response_model=SubjectRead)
async def update_subject(
    id: uuid.UUID,
    body: SubjectUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = SubjectService(db)
    return await svc.update(id, body.model_dump(exclude_none=True))


# ---------------------------------------------------------------------------
# Grading Schemes
# ---------------------------------------------------------------------------

@router.get("/grading-schemes", response_model=list[GradingSchemeRead])
async def list_grading_schemes(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = GradingSchemeService(db)
    return await svc.list_all()


@router.post("/grading-schemes", response_model=GradingSchemeRead, status_code=201)
async def create_grading_scheme(
    body: GradingSchemeCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = GradingSchemeService(db)
    return await svc.create(body.model_dump())


@router.get("/grading-schemes/{id}", response_model=GradingSchemeRead)
async def get_grading_scheme(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = GradingSchemeService(db)
    return await svc.get(id)
