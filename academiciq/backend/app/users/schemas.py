"""Pydantic schemas for user management."""
from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    role_id: uuid.UUID
    department_id: uuid.UUID | None = None


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    is_active: bool | None = None
    department_id: uuid.UUID | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    mfa_enabled: bool
    last_login: datetime | None
    created_at: datetime
