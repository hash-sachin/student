"""User management service."""
from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError, NotFoundError
from app.core.security import hash_password
from app.database.models import User


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_all(self) -> Sequence[User]:
        r = await self._db.execute(
            select(User).where(User.is_deleted == False).order_by(User.full_name)
        )
        return r.scalars().all()

    async def get(self, id: uuid.UUID) -> User:
        r = await self._db.execute(
            select(User).where(User.id == id, User.is_deleted == False)
        )
        u = r.scalar_one_or_none()
        if not u:
            raise NotFoundError("User", id)
        return u

    async def create(self, data: dict) -> User:
        plain = data.pop("password")
        existing = await self._db.execute(
            select(User).where(User.email == data["email"].lower())
        )
        if existing.scalar_one_or_none():
            raise AlreadyExistsError(f"User with email '{data['email']}' already exists")
        data["email"] = data["email"].lower()
        data["hashed_password"] = hash_password(plain)
        user = User(**data)
        self._db.add(user)
        await self._db.flush()
        return user

    async def update(self, id: uuid.UUID, data: dict) -> User:
        user = await self.get(id)
        for k, v in data.items():
            if v is not None:
                setattr(user, k, v)
        await self._db.flush()
        return user

    async def soft_delete(self, id: uuid.UUID) -> None:
        user = await self.get(id)
        user.is_deleted = True
        user.is_active = False
        await self._db.flush()
