"""Notifications router."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.database.models import Notification
from app.database.session import get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    unread_only: bool = False,
):
    q = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        q = q.where(Notification.is_read == False)
    q = q.order_by(Notification.created_at.desc()).limit(50)
    r = await db.execute(q)
    notes = r.scalars().all()
    return [
        {
            "id": str(n.id),
            "type": n.type,
            "title": n.title,
            "body": n.body,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in notes
    ]


@router.patch("/{id}/read", status_code=204)
async def mark_read(
    id: uuid.UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await db.execute(
        update(Notification)
        .where(Notification.id == id, Notification.user_id == current_user.id)
        .values(is_read=True)
    )
    return None
