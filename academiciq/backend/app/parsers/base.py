"""
Parser interface and base classes.
All parsers implement the ResultParser protocol.
Selection chain: UniversitySpecificParser → GenericPDFParser → OCRParser
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ExtractedRecord:
    """A single extracted student-subject record from a PDF."""
    raw_register_number: str | None = None
    raw_subject_code: str | None = None
    raw_subject_name: str | None = None
    raw_internal_marks: str | None = None
    raw_external_marks: str | None = None
    raw_total_marks: str | None = None
    raw_grade: str | None = None
    raw_result_status: str | None = None
    is_absent: bool = False
    special_code: str | None = None

    # Provenance
    page_number: int | None = None
    bounding_box: dict | None = None
    line_reference: str | None = None
    extraction_method: str = "table"  # table | text | ocr
    confidence_score: float = 1.0
    raw_row: dict = field(default_factory=dict)  # original row for audit


class ResultParser(Protocol):
    """Interface every parser must implement."""
    name: str
    version: str
    last_confidence: float

    def can_parse(self, file_path: str) -> tuple[bool, float]:
        """
        Check if this parser can handle the given PDF.
        Returns (can_handle, confidence_score).
        """
        ...

    def extract(self, file_path: str) -> list[ExtractedRecord]:
        """
        Extract all student-subject records from the PDF.
        Must never raise silently — log errors and return partial results.
        """
        ...


class BaseParser:
    """Shared utilities for parsers."""
    name: str = "BaseParser"
    version: str = "1.0"
    last_confidence: float = 0.0

    def _normalize_marks(self, raw: str | None) -> tuple[float | None, bool]:
        """
        Normalize a marks string.
        Returns (float_value_or_None, is_absent).
        Absent codes: AB, ABS, ABSENT, -, --
        """
        if raw is None:
            return None, False
        stripped = raw.strip().upper()
        if stripped in ("AB", "ABS", "ABSENT", "-", "--", "A"):
            return None, True
        try:
            return float(stripped), False
        except ValueError:
            return None, False

    def _normalize_grade(self, raw: str | None) -> str | None:
        if raw is None:
            return None
        return raw.strip().upper() or None

    def _normalize_result_status(self, raw: str | None) -> str | None:
        if raw is None:
            return None
        s = raw.strip().upper()
        mapping = {
            "P": "PASS", "PASS": "PASS",
            "F": "FAIL", "FAIL": "FAIL",
            "W": "WITHHELD", "WH": "WITHHELD",
            "AB": "ABSENT", "ABS": "ABSENT",
            "MP": "MALPRACTICE",
            "EX": "EXEMPTED",
        }
        return mapping.get(s, s)
