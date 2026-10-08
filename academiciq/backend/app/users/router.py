"""Users management router — ADMIN / SUPER_ADMIN only."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.exceptions import PermissionDeniedError
from app.database.models import UserRole
from app.database.session import get_db
from app.users.schemas import UserCreate, UserRead, UserUpdate
from app.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def _require_admin(current_user):
    if current_user.role.name not in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value):
        raise PermissionDeniedError("manage users")


@router.get("", response_model=list[UserRead])
async def list_users(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _require_admin(current_user)
    svc = UserService(db)
    return await svc.list_all()


@router.post("", response_model=UserRead, status_code=201)
async def create_user(
    body: UserCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _require_admin(current_user)
    svc = UserService(db)
    return await svc.create(body.model_dump())


@router.get("/{id}", response_model=UserRead)
async def get_user(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _require_admin(current_user)
    svc = UserService(db)
    return await svc.get(id)


@router.put("/{id}", response_model=UserRead)
async def update_user(
    id: uuid.UUID,
    body: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    _require_admin(current_user)
    svc = UserService(db)
    return await svc.update(id, body.model_dump(exclude_none=True))


@router.delete("/{id}", status_code=204)
async def delete_user(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.role.name != UserRole.SUPER_ADMIN.value:
        raise PermissionDeniedError("delete users")
    svc = UserService(db)
    await svc.soft_delete(id)
    return None
