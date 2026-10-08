"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.base import Base
from app.database.models import Role, User, UserRole
from app.core.security import create_access_token, hash_password
from app.main import app
from app.database.session import get_db

# Test database URL (in-memory SQLite for unit tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_academiciq.db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with DB session override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_role(db_session: AsyncSession) -> Role:
    role = Role(name=UserRole.ADMIN.value, description="Admin")
    db_session.add(role)
    await db_session.flush()
    return role


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, admin_role: Role) -> User:
    user = User(
        email="testadmin@test.com",
        hashed_password=hash_password("Test@123!"),
        full_name="Test Admin",
        role_id=admin_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_token(admin_user: User) -> str:
    return create_access_token(str(admin_user.id), extra={"role": "ADMIN"})


@pytest_asyncio.fixture
async def auth_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}
