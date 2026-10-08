# ADR-004: Password Hashing Algorithm — Argon2id

**Date:** 2026-10-07  
**Status:** Accepted  
**Alternatives considered:** bcrypt, scrypt, PBKDF2

## Decision

Use **Argon2id** via `argon2-cffi` for all password hashing.

Parameters:
- `time_cost=2` (iterations)
- `memory_cost=65536` (64 MB)
- `parallelism=2`
- `hash_len=32`
- `salt_len=16` (random per hash)

## Rationale

- Argon2id won the Password Hashing Competition (2015) and is recommended by OWASP as the first choice for password hashing.
- Memory-hardness (`memory_cost=65536`) makes GPU/ASIC cracking significantly more expensive than bcrypt.
- The `id` variant (hybrid of `i` and `d`) protects against both side-channel and GPU attacks.
- `argon2-cffi` is the well-maintained Python binding with no native C compilation issues on modern platforms.

## Consequences

- `app/core/security.py` exposes `hash_password()`, `verify_password()`, and `needs_rehash()`.
- On successful login, if `needs_rehash()` returns True the hash is transparently upgraded.
- bcrypt is NOT used. `passlib` is listed as a dev dependency only for migration compatibility if needed.
