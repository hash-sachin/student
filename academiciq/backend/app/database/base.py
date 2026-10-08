"""SQLAlchemy declarative base and common mixins."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, JSON, func, String, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ---------------------------------------------------------------------------
# Dialect-aware JSONB: uses PostgreSQL JSONB when available, falls back to
# standard JSON for SQLite and other databases.
# ---------------------------------------------------------------------------
class JSONB(TypeDecorator):
    """
    Dialect-aware JSON column.
    - PostgreSQL  → native JSONB (indexed, operators, GIN support)
    - SQLite/other → standard JSON (for local dev and testing)
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(JSON())


# ---------------------------------------------------------------------------
# Dialect-aware UUID: uses PostgreSQL native UUID when available, falls back
# to a string representation for SQLite.
# ---------------------------------------------------------------------------
class UUID(TypeDecorator):
    """
    Dialect-aware UUID column.
    - PostgreSQL → native UUID
    - SQLite/other → CHAR(36) string
    """
    impl = String
    cache_ok = True

    def __init__(self, as_uuid: bool = True):
        self.as_uuid = as_uuid
        super().__init__(36)

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=self.as_uuid))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        # SQLite: store as lowercase string
        return str(value).lower()

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if self.as_uuid and not isinstance(value, uuid.UUID):
            return uuid.UUID(str(value))
        return value


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Adds created_at and updated_at columns."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """UUID v4 primary key — dialect-aware."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class SoftDeleteMixin:
    """Soft deletion with optional legal-hold flag."""
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    is_deleted: Mapped[bool] = mapped_column(default=False, nullable=False)
