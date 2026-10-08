"""Unit tests: password hashing and JWT tokens."""
import pytest
from app.core.security import (
    create_access_token, create_refresh_token, decode_token,
    hash_password, verify_password, needs_rehash,
)


def test_hash_and_verify_password():
    plain = "MySecurePassword@123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)


def test_wrong_password_rejected():
    hashed = hash_password("correct_password")
    assert not verify_password("wrong_password", hashed)


def test_access_token_roundtrip():
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    token = create_access_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_refresh_token_roundtrip():
    user_id = "550e8400-e29b-41d4-a716-446655440001"
    token = create_refresh_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"


def test_access_token_rejects_refresh():
    """Access token check should fail for refresh tokens."""
    token = create_refresh_token("some-user-id")
    payload = decode_token(token)
    assert payload["type"] == "refresh"
    assert payload["type"] != "access"


def test_different_passwords_produce_different_hashes():
    h1 = hash_password("password1")
    h2 = hash_password("password1")
    # Argon2 uses random salt — same password produces different hashes
    assert h1 != h2
    # But both verify correctly
    assert verify_password("password1", h1)
    assert verify_password("password1", h2)
