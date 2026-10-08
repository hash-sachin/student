"""FastAPI auth dependencies."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthenticationError
from app.core.security import decode_token
from app.database.models import User, Role
from app.database.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Extract and validate the JWT bearer token, return the User object."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    if user.locked_until and user.locked_until > datetime.now(tz=timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is locked until {user.locked_until.isoformat()}",
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
