"""Audit log API router — read-only, SUPER_ADMIN / ADMIN only."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.models import AuditLog, UserRole
from app.database.session import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
async def list_audit_logs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    action: str | None = None,
    entity_type: str | None = None,
    user_id: uuid.UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    """
    Returns immutable audit log entries.
    Access: SUPER_ADMIN and ADMIN only (enforced here; full RBAC in service layer).
    """
    from app.core.exceptions import PermissionDeniedError
    if current_user.role.name not in (UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value):
        raise PermissionDeniedError("read audit logs")

    q = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        q = q.where(AuditLog.action == action)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)

    offset = (page - 1) * page_size
    q = q.offset(offset).limit(page_size)
    r = await db.execute(q)
    logs = r.scalars().all()

    return [
        {
            "id": str(log.id),
            "action": log.action,
            "user_id": str(log.user_id) if log.user_id else None,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "ip_address": log.ip_address,
            "request_id": log.request_id,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
