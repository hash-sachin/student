"""
Grading service — re-exports GradingSchemeService from academics.
The grading scheme CRUD lives in app.academics.service to keep all
master-data management in one place. This module exists for explicit
import compatibility.
"""
from app.academics.service import GradingSchemeService  # noqa: F401

__all__ = ["GradingSchemeService"]
