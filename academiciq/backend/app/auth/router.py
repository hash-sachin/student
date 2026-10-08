"""Auth endpoints: login, refresh, logout."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr

from app.auth.service import AuthService
from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate with email + password. Returns JWT access + refresh tokens."""
    service = AuthService(db)
    ip = request.client.host if request.client else None
    request_id = request.headers.get("X-Request-ID")
    return await service.login(body.email, body.password, ip_address=ip, request_id=request_id)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Exchange a valid refresh token for a new access token."""
    service = AuthService(db)
    return await service.refresh(body.refresh_token)


@router.post("/logout", status_code=204)
async def logout(current_user: CurrentUser):
    """
    Logout endpoint. Client must discard the tokens.
    (Server-side token revocation requires a blocklist — add in Phase 10 if needed.)
    """
    return None
