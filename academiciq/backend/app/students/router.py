"""Students API router."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.students.schemas import StudentCreate, StudentListResponse, StudentRead, StudentUpdate
from app.students.service import StudentService

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=StudentListResponse)
async def list_students(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department_id: uuid.UUID | None = None,
    program_id: uuid.UUID | None = None,
    batch_id: uuid.UUID | None = None,
    status: str | None = None,
    search: str | None = None,
):
    svc = StudentService(db)
    items, total = await svc.list_students(
        page=page,
        page_size=page_size,
        department_id=department_id,
        program_id=program_id,
        batch_id=batch_id,
        status=status,
        search=search,
    )
    return StudentListResponse(
        items=[StudentRead.model_validate(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=StudentRead, status_code=201)
async def create_student(
    body: StudentCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = StudentService(db)
    return await svc.create(body.model_dump())


@router.get("/{id}", response_model=StudentRead)
async def get_student(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = StudentService(db)
    return await svc.get(id)


@router.put("/{id}", response_model=StudentRead)
async def update_student(
    id: uuid.UUID,
    body: StudentUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    svc = StudentService(db)
    return await svc.update(id, body.model_dump(exclude_none=True))
