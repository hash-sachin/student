"""Authentication service — login, refresh, logout."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AccountLockedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    needs_rehash,
    verify_password,
    hash_password,
)
from app.database.models import AuditLog, User

logger = structlog.get_logger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def login(
        self,
        email: str,
        password: str,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> dict:
        """
        Authenticate a user. Returns access + refresh tokens.
        Enforces account lockout after MAX_LOGIN_ATTEMPTS failures.
        """
        result = await self._db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.email == email.lower(), User.is_deleted == False)
        )
        user: User | None = result.scalar_one_or_none()

        # Timing-safe: always compute verify even if user not found
        dummy_hash = "$argon2id$v=19$m=65536,t=2,p=2$AAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # noqa

        if user is None:
            verify_password(password, dummy_hash)  # timing normalization
            await self._audit(None, "LOGIN_FAILED", ip=ip_address, rid=request_id,
                              detail={"reason": "user_not_found", "email": email})
            raise AuthenticationError("Invalid email or password")

        # Check lockout
        now = datetime.now(tz=timezone.utc)
        if user.locked_until and user.locked_until > now:
            raise AccountLockedError(
                f"Account is locked until {user.locked_until.isoformat()}"
            )

        if not verify_password(password, user.hashed_password):
            # Increment failure count
            new_count = user.failed_login_count + 1
            lock_until = None
            if new_count >= settings.MAX_LOGIN_ATTEMPTS:
                lock_until = now + timedelta(minutes=settings.LOCKOUT_MINUTES)
                logger.warning("account_locked", user_id=str(user.id), email=email)

            await self._db.execute(
                update(User)
                .where(User.id == user.id)
                .values(failed_login_count=new_count, locked_until=lock_until)
            )
            await self._db.commit()
            await self._audit(user.id, "LOGIN_FAILED", ip=ip_address, rid=request_id,
                              detail={"reason": "bad_password", "attempt": new_count})
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        # Success — reset failure count
        await self._db.execute(
            update(User)
            .where(User.id == user.id)
            .values(
                failed_login_count=0,
                locked_until=None,
                last_login=now,
            )
        )

        # Rehash if Argon2 parameters have been updated
        if needs_rehash(user.hashed_password):
            new_hash = hash_password(password)
            await self._db.execute(
                update(User)
                .where(User.id == user.id)
                .values(hashed_password=new_hash, password_changed_at=now)
            )

        await self._db.commit()

        extra = {"role": user.role.name, "email": user.email}
        access_token = create_access_token(str(user.id), extra=extra)
        refresh_token = create_refresh_token(str(user.id))

        await self._audit(user.id, "LOGIN_SUCCESS", ip=ip_address, rid=request_id)

        logger.info("login_success", user_id=str(user.id), role=user.role.name)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def refresh(self, refresh_token: str) -> dict:
        """Issue a new access token from a valid refresh token."""
        from jose import JWTError

        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise AuthenticationError("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid refresh token")

        result = await self._db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == uuid.UUID(user_id), User.is_deleted == False, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise AuthenticationError("User not found")

        extra = {"role": user.role.name, "email": user.email}
        access_token = create_access_token(str(user.id), extra=extra)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def _audit(
        self,
        user_id: uuid.UUID | None,
        action: str,
        ip: str | None = None,
        rid: str | None = None,
        detail: dict | None = None,
    ) -> None:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type="user",
            entity_id=user_id,
            new_value=detail,
            ip_address=ip,
            request_id=rid,
        )
        self._db.add(log)
