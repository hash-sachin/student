"""
GenericPDFParser — heuristic table extraction using pdfplumber.
Falls back to OCRParser if table extraction confidence is too low.
"""
from __future__ import annotations

import re
from typing import Any

import pdfplumber
import structlog

from app.parsers.base import BaseParser, ExtractedRecord

logger = structlog.get_logger(__name__)

# Minimum confidence to use generic extraction
MIN_TABLE_CONFIDENCE = 0.5

# Column header patterns (case-insensitive)
REGISTER_PATTERNS = re.compile(r"reg(ister)?\s*(no|num|number)?", re.IGNORECASE)
SUBJECT_CODE_PATTERNS = re.compile(r"sub(ject)?\s*(code|no)?", re.IGNORECASE)
INTERNAL_PATTERNS = re.compile(r"int(ernal)?|ia|ca|cia", re.IGNORECASE)
EXTERNAL_PATTERNS = re.compile(r"ext(ernal)?|theory|ee|sem", re.IGNORECASE)
TOTAL_PATTERNS = re.compile(r"total|tot", re.IGNORECASE)
GRADE_PATTERNS = re.compile(r"grade", re.IGNORECASE)
STATUS_PATTERNS = re.compile(r"result|status|pass|fail", re.IGNORECASE)


class GenericPDFParser(BaseParser):
    name = "GenericPDFParser"
    version = "1.0"

    def can_parse(self, file_path: str) -> tuple[bool, float]:
        """Check if pdfplumber can find tables with recognizable headers."""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages[:3]:  # check first 3 pages
                    tables = page.extract_tables()
                    for table in tables:
                        if table and len(table) > 1:
                            header = [str(c).lower() if c else "" for c in table[0]]
                            col_map = self._detect_columns(header)
                            if col_map.get("register") is not None:
                                confidence = self._estimate_confidence(col_map)
                                return True, confidence
            return False, 0.0
        except Exception as e:
            logger.warning("generic_parser_can_parse_error", error=str(e))
            return False, 0.0

    def extract(self, file_path: str) -> list[ExtractedRecord]:
        records: list[ExtractedRecord] = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables()
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        header = [str(c).lower().strip() if c else "" for c in table[0]]
                        col_map = self._detect_columns(header)
                        if col_map.get("register") is None:
                            continue

                        for row_idx, row in enumerate(table[1:], start=1):
                            rec = self._parse_row(row, col_map, page_num, row_idx)
                            if rec:
                                records.append(rec)
        except Exception as e:
            logger.error("generic_parser_extract_error", error=str(e), file=file_path)

        self.last_confidence = self._estimate_record_quality(records)
        logger.info("generic_parser_extracted", count=len(records), file=file_path)
        return records

    def _detect_columns(self, header: list[str]) -> dict[str, int | None]:
        """Map semantic column names to column indices."""
        result: dict[str, int | None] = {
            "register": None,
            "subject_code": None,
            "subject_name": None,
            "internal": None,
            "external": None,
            "total": None,
            "grade": None,
            "status": None,
        }
        for i, h in enumerate(header):
            if result["register"] is None and REGISTER_PATTERNS.search(h):
                result["register"] = i
            elif result["subject_code"] is None and SUBJECT_CODE_PATTERNS.search(h):
                result["subject_code"] = i
            elif result["internal"] is None and INTERNAL_PATTERNS.search(h):
                result["internal"] = i
            elif result["external"] is None and EXTERNAL_PATTERNS.search(h):
                result["external"] = i
            elif result["total"] is None and TOTAL_PATTERNS.search(h):
                result["total"] = i
            elif result["grade"] is None and GRADE_PATTERNS.search(h):
                result["grade"] = i
            elif result["status"] is None and STATUS_PATTERNS.search(h):
                result["status"] = i
        return result

    def _estimate_confidence(self, col_map: dict) -> float:
        found = sum(1 for v in col_map.values() if v is not None)
        return min(found / len(col_map), 1.0)

    def _parse_row(
        self,
        row: list,
        col_map: dict[str, int | None],
        page_num: int,
        row_idx: int,
    ) -> ExtractedRecord | None:
        def get(key: str) -> str | None:
            idx = col_map.get(key)
            if idx is None or idx >= len(row):
                return None
            v = row[idx]
            return str(v).strip() if v is not None else None

        reg = get("register")
        if not reg:
            return None  # skip blank rows

        raw_int = get("internal")
        raw_ext = get("external")
        raw_tot = get("total")

        int_val, int_absent = self._normalize_marks(raw_int)
        ext_val, ext_absent = self._normalize_marks(raw_ext)
        tot_val, tot_absent = self._normalize_marks(raw_tot)
        is_absent = int_absent and ext_absent

        return ExtractedRecord(
            raw_register_number=reg,
            raw_subject_code=get("subject_code"),
            raw_subject_name=None,  # often not in same table row
            raw_internal_marks=raw_int,
            raw_external_marks=raw_ext,
            raw_total_marks=raw_tot,
            raw_grade=get("grade"),
            raw_result_status=get("status"),
            is_absent=is_absent,
            page_number=page_num,
            extraction_method="table",
            confidence_score=0.85,
            raw_row={str(i): v for i, v in enumerate(row)},
        )

    def _estimate_record_quality(self, records: list[ExtractedRecord]) -> float:
        if not records:
            return 0.0
        complete = sum(
            1 for r in records
            if r.raw_register_number and (r.raw_total_marks or r.is_absent)
        )
        return complete / len(records)
