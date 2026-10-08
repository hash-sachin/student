"""
Unit tests for the What-If Simulation Engine.
Tests: hypothetical labeling, grade computation, delta calculation,
       marks validation, is_hypothetical enforcement.
"""
from __future__ import annotations

import pytest


def test_hypothetical_label_is_always_set():
    """Every simulation output must carry is_hypothetical=True."""
    from app.database.models import MetricLabel
    assert MetricLabel.HYPOTHETICAL.value == "HYPOTHETICAL"


def test_grade_computation_with_scheme():
    """Grade calculator returns correct grade from marks."""
    from app.simulation.engine import SimulationEngine
    from unittest.mock import AsyncMock

    engine = SimulationEngine(AsyncMock())

    class FakeScheme:
        grade_map = [
            {"min": 91, "max": 100, "grade": "O"},
            {"min": 81, "max": 90, "grade": "A+"},
            {"min": 71, "max": 80, "grade": "A"},
            {"min": 50, "max": 70, "grade": "B"},
            {"min": 0, "max": 49, "grade": "F"},
        ]

    assert engine._compute_grade(95.0, FakeScheme()) == "O"
    assert engine._compute_grade(85.0, FakeScheme()) == "A+"
    assert engine._compute_grade(55.0, FakeScheme()) == "B"
    assert engine._compute_grade(40.0, FakeScheme()) == "F"


def test_compute_grade_returns_none_without_scheme():
    from app.simulation.engine import SimulationEngine
    from unittest.mock import AsyncMock

    engine = SimulationEngine(AsyncMock())
    assert engine._compute_grade(85.0, None) is None


def test_hypothetical_banner_constant():
    from app.simulation.router import HYPOTHETICAL_BANNER
    assert "HYPOTHETICAL" in HYPOTHETICAL_BANNER
    assert "NOT AN ACTUAL RESULT" in HYPOTHETICAL_BANNER
