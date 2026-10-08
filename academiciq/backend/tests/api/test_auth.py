"""API integration tests for auth endpoints."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "AcademicIQ" in data["app"]


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testadmin@test.com", "password": "wrong_password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@nowhere.com", "password": "whatever"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client):
    """Unauthenticated request to students should return 401."""
    response = await client.get("/api/v1/students")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_with_valid_token(client, auth_headers):
    """Authenticated request should not return 401."""
    response = await client.get("/api/v1/students", headers=auth_headers)
    # 200 or 422 (no students yet) — not 401
    assert response.status_code != 401
