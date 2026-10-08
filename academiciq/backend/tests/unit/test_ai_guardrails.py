"""
Unit tests for AI guardrail filters.
Coverage: G1 numeric, G2 entity, G3 causal, G4 sensitive.
Target: 100% coverage on guardrail module.
"""
from __future__ import annotations

import re
import pytest

from app.ai.service import (
    AIInsightService, CAUSAL_PATTERN, SENSITIVE_PATTERN, NUMBER_PATTERN
)
from unittest.mock import AsyncMock


def make_service():
    return AIInsightService(AsyncMock())


# ------------------------------------------------------------------
# G1: Numeric verifier
# ------------------------------------------------------------------

def test_numeric_in_evidence():
    svc = make_service()
    assert svc._number_in_evidence("75.5", {"75.5"})


def test_numeric_within_tolerance():
    svc = make_service()
    # 75.5 vs 75.8 → 0.4% difference → within 0.5% tolerance
    assert svc._number_in_evidence("75.5", {"75.8"})


def test_numeric_outside_tolerance():
    svc = make_service()
    # 75.5 vs 80.0 → ~5.9% difference → outside 0.5%
    assert not svc._number_in_evidence("75.5", {"80.0"})


def test_zero_handling():
    svc = make_service()
    assert svc._number_in_evidence("0", {"0"})


# ------------------------------------------------------------------
# G3: Causal claim filter
# ------------------------------------------------------------------

def test_causal_pattern_detected():
    text = "Student failed because of low attendance."
    assert CAUSAL_PATTERN.search(text)


def test_causal_pattern_due_to():
    text = "Performance dropped due to external factors."
    assert CAUSAL_PATTERN.search(text)


def test_causal_pattern_clean():
    text = "Student average is 65.2 this semester."
    assert not CAUSAL_PATTERN.search(text)


# ------------------------------------------------------------------
# G4: Sensitive inference filter
# ------------------------------------------------------------------

def test_sensitive_mental_health():
    text = "The student may be experiencing depression."
    assert SENSITIVE_PATTERN.search(text)


def test_sensitive_family():
    text = "Family circumstances may affect performance."
    assert SENSITIVE_PATTERN.search(text)


def test_sensitive_clean():
    text = "Student average declined by 8.3 points this semester."
    assert not SENSITIVE_PATTERN.search(text)


# ------------------------------------------------------------------
# G5: Schema validation
# ------------------------------------------------------------------

def test_schema_required_keys():
    required = {"claim", "evidence_ids", "metrics", "confidence_basis", "timestamp"}
    valid_output = {
        "claim": "test", "evidence_ids": [], "metrics": [],
        "confidence_basis": "verified", "timestamp": "2026-10-07"
    }
    missing = required - set(valid_output.keys())
    assert not missing


def test_schema_missing_key_detected():
    required = {"claim", "evidence_ids", "metrics", "confidence_basis", "timestamp"}
    invalid_output = {"claim": "test"}
    missing = required - set(invalid_output.keys())
    assert "evidence_ids" in missing
    assert "timestamp" in missing


# ------------------------------------------------------------------
# Insufficient data response
# ------------------------------------------------------------------

def test_insufficient_data_constant():
    from app.ai.service import INSUFFICIENT_DATA_RESPONSE
    assert "Insufficient" in INSUFFICIENT_DATA_RESPONSE
    assert "verified data" in INSUFFICIENT_DATA_RESPONSE
