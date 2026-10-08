"""
Audit service — append-only audit log writer.
Every write goes through this service; direct INSERT only, never UPDATE/DELETE.
Covers all actions listed in spec Section 18.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AuditLog

logger = structlog.get_logger(__name__)

# Canonical action names (spec Section 18)
class AuditAction:
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    UPLOAD_INITIATED = "UPLOAD_INITIATED"
    UPLOAD_COMMITTED = "UPLOAD_COMMITTED"
    UPLOAD_REJECTED = "UPLOAD_REJECTED"
    RECORD_UPDATED = "RECORD_UPDATED"
    RESULT_COMMITTED = "RESULT_COMMITTED"
    STUDENT_CREATED = "STUDENT_CREATED"
    STUDENT_UPDATED = "STUDENT_UPDATED"
    ATTENTION_CALCULATED = "ATTENTION_CALCULATED"
    INTERVENTION_CREATED = "INTERVENTION_CREATED"
    INTERVENTION_REVIEWED = "INTERVENTION_REVIEWED"
    SIMULATION_RUN = "SIMULATION_RUN"
    AI_GENERATED = "AI_GENERATED"
    REPORT_GENERATED = "REPORT_GENERATED"
    GRADING_SCHEME_CREATED = "GRADING_SCHEME_CREATED"
    GRADING_SCHEME_UPDATED = "GRADING_SCHEME_UPDATED"
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"


class AuditService:
    """
    Append-only audit log service.
    Never call UPDATE or DELETE on audit_logs table.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def log(
        self,
        action: str,
        user_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        old_value: dict | None = None,
        new_value: dict | None = None,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        """Write an immutable audit record."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            request_id=request_id,
        )
        self._db.add(entry)
        await self._db.flush()
        logger.info(
            "audit_log",
            action=action,
            user_id=str(user_id) if user_id else None,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
        )
        return entry
