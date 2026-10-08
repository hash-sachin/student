"""
Unit tests for the Academic Attention Engine.
Tests: factor computation, score bands, reproducibility, partial score handling.
Coverage target: 100% on scoring module.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.database.models import AttentionBand, ResultStatus
from app.intelligence.attention_engine import (
    ALGORITHM_VERSION, AttentionEngine, DEFAULT_SCORING_CONFIG, FactorResult
)


def make_engine() -> AttentionEngine:
    db = AsyncMock()
    engine = AttentionEngine(db)
    return engine


# ------------------------------------------------------------------
# F1: Semester decline
# ------------------------------------------------------------------

def test_f1_no_decline():
    engine = make_engine()
    result = engine._f1_semester_decline(75.0, [70.0], DEFAULT_SCORING_CONFIG)
    assert result.points == 0
    assert not result.skipped


def test_f1_small_decline():
    engine = make_engine()
    result = engine._f1_semester_decline(64.0, [70.0], DEFAULT_SCORING_CONFIG)
    # drop = 70 - 64 = 6 → 8 points
    assert result.points == 8


def test_f1_medium_decline():
    engine = make_engine()
    result = engine._f1_semester_decline(58.0, [70.0], DEFAULT_SCORING_CONFIG)
    # drop = 12 → 14 points
    assert result.points == 14


def test_f1_large_decline():
    engine = make_engine()
    result = engine._f1_semester_decline(50.0, [70.0], DEFAULT_SCORING_CONFIG)
    # drop = 20 → 20 points
    assert result.points == 20


def test_f1_no_history():
    engine = make_engine()
    result = engine._f1_semester_decline(70.0, [], DEFAULT_SCORING_CONFIG)
    assert result.skipped
    assert result.points == 0


def test_f1_no_current_average():
    engine = make_engine()
    result = engine._f1_semester_decline(None, [70.0], DEFAULT_SCORING_CONFIG)
    assert result.skipped


# ------------------------------------------------------------------
# F2: Failed subjects
# ------------------------------------------------------------------

def make_result(status: str, is_absent: bool = False):
    r = MagicMock()
    r.result_status = ResultStatus(status) if status else None
    r.is_absent = is_absent
    r.total_marks = 45.0
    return r


def test_f2_no_failures():
    engine = make_engine()
    results = [make_result("PASS") for _ in range(5)]
    fr = engine._f2_failed_subjects(results, DEFAULT_SCORING_CONFIG)
    assert fr.points == 0


def test_f2_one_failure():
    engine = make_engine()
    results = [make_result("FAIL")] + [make_result("PASS") for _ in range(4)]
    fr = engine._f2_failed_subjects(results, DEFAULT_SCORING_CONFIG)
    assert fr.points == 8


def test_f2_two_failures():
    engine = make_engine()
    results = [make_result("FAIL")] * 2 + [make_result("PASS")] * 3
    fr = engine._f2_failed_subjects(results, DEFAULT_SCORING_CONFIG)
    assert fr.points == 14


def test_f2_three_or_more_failures():
    engine = make_engine()
    results = [make_result("FAIL")] * 3 + [make_result("PASS")] * 2
    fr = engine._f2_failed_subjects(results, DEFAULT_SCORING_CONFIG)
    assert fr.points == 20


def test_f2_absent_not_counted_as_fail():
    engine = make_engine()
    results = [make_result("ABSENT", is_absent=True)] * 5
    fr = engine._f2_failed_subjects(results, DEFAULT_SCORING_CONFIG)
    assert fr.points == 0


# ------------------------------------------------------------------
# F6: Low performance
# ------------------------------------------------------------------

def test_f6_above_threshold():
    engine = make_engine()
    fr = engine._f6_low_performance(75.0, 50, DEFAULT_SCORING_CONFIG)
    assert fr.points == 0


def test_f6_borderline():
    engine = make_engine()
    fr = engine._f6_low_performance(55.0, 50, DEFAULT_SCORING_CONFIG)
    assert fr.points == 4


def test_f6_low():
    engine = make_engine()
    fr = engine._f6_low_performance(45.0, 50, DEFAULT_SCORING_CONFIG)
    assert fr.points == 7


def test_f6_very_low():
    engine = make_engine()
    fr = engine._f6_low_performance(35.0, 50, DEFAULT_SCORING_CONFIG)
    assert fr.points == 10


# ------------------------------------------------------------------
# Band classification
# ------------------------------------------------------------------

def test_band_normal():
    engine = make_engine()
    assert engine._score_to_band(0, DEFAULT_SCORING_CONFIG) == AttentionBand.NORMAL
    assert engine._score_to_band(24, DEFAULT_SCORING_CONFIG) == AttentionBand.NORMAL


def test_band_monitor():
    engine = make_engine()
    assert engine._score_to_band(25, DEFAULT_SCORING_CONFIG) == AttentionBand.MONITOR
    assert engine._score_to_band(49, DEFAULT_SCORING_CONFIG) == AttentionBand.MONITOR


def test_band_attention():
    engine = make_engine()
    assert engine._score_to_band(50, DEFAULT_SCORING_CONFIG) == AttentionBand.ATTENTION
    assert engine._score_to_band(74, DEFAULT_SCORING_CONFIG) == AttentionBand.ATTENTION


def test_band_high_attention():
    engine = make_engine()
    assert engine._score_to_band(75, DEFAULT_SCORING_CONFIG) == AttentionBand.HIGH_ATTENTION
    assert engine._score_to_band(100, DEFAULT_SCORING_CONFIG) == AttentionBand.HIGH_ATTENTION


# ------------------------------------------------------------------
# Score reproducibility (H4)
# ------------------------------------------------------------------

def test_score_deterministic():
    """Same inputs + same config → same points. (H4 reproducibility)"""
    engine = make_engine()
    # F1 twice with same inputs
    r1 = engine._f1_semester_decline(60.0, [78.0], DEFAULT_SCORING_CONFIG)
    r2 = engine._f1_semester_decline(60.0, [78.0], DEFAULT_SCORING_CONFIG)
    assert r1.points == r2.points


# ------------------------------------------------------------------
# Metric label
# ------------------------------------------------------------------

def test_attention_score_labeled_estimated():
    """Attention score result must carry ESTIMATED label."""
    from app.database.models import MetricLabel
    from app.intelligence.attention_engine import AttentionScoreResult
    result = AttentionScoreResult(
        student_id=uuid.uuid4(),
        examination_id=uuid.uuid4(),
        raw_score=55.0,
        band=AttentionBand.ATTENTION,
        factors=[],
        is_partial_score=False,
        missing_factors=[],
        algorithm_version=ALGORITHM_VERSION,
        scoring_config_id=None,
        input_snapshot_hash="abc",
    )
    assert result.metric_label == MetricLabel.ESTIMATED.value
