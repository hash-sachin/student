"""Pydantic schemas for students."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    register_number: str = Field(..., max_length=50)
    university_register_number: str | None = Field(None, max_length=50)
    name: str = Field(..., max_length=255)
    department_id: uuid.UUID
    program_id: uuid.UUID
    batch_id: uuid.UUID
    admission_year: int = Field(..., ge=2000, le=2100)
    status: str = Field("ACTIVE", pattern="^(ACTIVE|DISCONTINUED|GRADUATED|ON_LEAVE)$")


class StudentUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    university_register_number: str | None = None
    status: str | None = Field(None, pattern="^(ACTIVE|DISCONTINUED|GRADUATED|ON_LEAVE)$")


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    register_number: str
    university_register_number: str | None
    name: str
    department_id: uuid.UUID
    program_id: uuid.UUID
    batch_id: uuid.UUID
    admission_year: int
    status: str
    created_at: datetime
    updated_at: datetime


class StudentListResponse(BaseModel):
    items: list[StudentRead]
    total: int
    page: int
    page_size: int
