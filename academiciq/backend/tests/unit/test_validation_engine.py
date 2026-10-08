"""Unit tests for validation engine edge cases."""
from __future__ import annotations

import pytest
from app.validation.engine import ValidationEngine
from unittest.mock import AsyncMock


def make_engine():
    db = AsyncMock()
    return ValidationEngine(db)


def test_parse_marks_normal():
    engine = make_engine()
    val, absent = engine._parse_marks("75")
    assert val == 75.0
    assert not absent


def test_parse_marks_absent():
    engine = make_engine()
    for code in ("AB", "ABS", "ABSENT", "-", "--", "A"):
        val, absent = engine._parse_marks(code)
        assert val is None
        assert absent, f"Expected absent=True for code '{code}'"


def test_parse_marks_float():
    engine = make_engine()
    val, absent = engine._parse_marks("78.5")
    assert val == 78.5
    assert not absent


def test_parse_marks_invalid():
    engine = make_engine()
    val, absent = engine._parse_marks("??")
    assert val is None
    assert not absent


def test_parse_grade_uppercase():
    engine = make_engine()
    assert engine._parse_grade("  a+  ") == "A+"
    assert engine._parse_grade(None) is None


def test_parse_result_status_mapping():
    engine = make_engine()
    assert engine._parse_result_status("P") == "PASS"
    assert engine._parse_result_status("F") == "FAIL"
    assert engine._parse_result_status("AB") == "ABSENT"
    assert engine._parse_result_status("WH") == "WITHHELD"
    assert engine._parse_result_status(None) is None


def test_grade_from_scheme():
    engine = make_engine()

    class FakeScheme:
        grade_map = [
            {"min": 90, "max": 100, "grade": "O"},
            {"min": 50, "max": 89, "grade": "B"},
            {"min": 0, "max": 49, "grade": "F"},
        ]

    assert engine._compute_grade(95.0, FakeScheme()) == "O"
    assert engine._compute_grade(60.0, FakeScheme()) == "B"
    assert engine._compute_grade(40.0, FakeScheme()) == "F"
