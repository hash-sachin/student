"""Domain exceptions for AcademicIQ."""
from __future__ import annotations


class AcademicIQError(Exception):
    """Base exception."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "An unexpected error occurred") -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AcademicIQError):
    status_code = 404
    error_code = "NOT_FOUND"

    def __init__(self, resource: str = "Resource", id: str | int | None = None) -> None:
        msg = f"{resource} not found" + (f": {id}" if id is not None else "")
        super().__init__(msg)


class AlreadyExistsError(AcademicIQError):
    status_code = 409
    error_code = "ALREADY_EXISTS"


class PermissionDeniedError(AcademicIQError):
    status_code = 403
    error_code = "PERMISSION_DENIED"

    def __init__(self, action: str = "perform this action") -> None:
        super().__init__(f"You do not have permission to {action}")


class AuthenticationError(AcademicIQError):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"


class AccountLockedError(AcademicIQError):
    status_code = 423
    error_code = "ACCOUNT_LOCKED"


class ValidationError(AcademicIQError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class DuplicateUploadError(AcademicIQError):
    status_code = 409
    error_code = "DUPLICATE_UPLOAD"


class InsufficientDataError(AcademicIQError):
    status_code = 422
    error_code = "INSUFFICIENT_DATA"
