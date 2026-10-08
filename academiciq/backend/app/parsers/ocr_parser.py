"""
OCRParser — fallback using pytesseract for scanned/image-based PDFs.
ADR-005: Tesseract chosen; PaddleOCR is an upgrade path for complex layouts.
"""
from __future__ import annotations

import re
from pathlib import Path

import structlog

from app.parsers.base import BaseParser, ExtractedRecord

logger = structlog.get_logger(__name__)

# Regex to detect register-number-like patterns (adapt per university plugin)
REGISTER_PATTERN = re.compile(r"\b\d{2}[A-Z]{2,5}\d{3,5}\b")
MARKS_PATTERN = re.compile(r"\b(\d{1,3}|AB|ABS)\b", re.IGNORECASE)


class OCRParser(BaseParser):
    name = "OCRParser"
    version = "1.0"

    def can_parse(self, file_path: str) -> tuple[bool, float]:
        """OCR parser is always the last-resort fallback."""
        return True, 0.3  # low confidence — fallback only

    def extract(self, file_path: str) -> list[ExtractedRecord]:
        """
        Convert PDF pages to images and run Tesseract OCR.
        Returns extracted records with is_low_confidence flag.
        """
        records: list[ExtractedRecord] = []
        try:
            import pytesseract
            import fitz  # PyMuPDF
            from PIL import Image
            import io

            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc, start=1):
                # Render page to image at 300 DPI for better OCR
                mat = fitz.Matrix(300 / 72, 300 / 72)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))

                text = pytesseract.image_to_string(img, config="--psm 6")
                page_records = self._parse_text(text, page_num)
                records.extend(page_records)
                logger.debug("ocr_page", page=page_num, records=len(page_records))

        except ImportError as e:
            logger.error("ocr_import_error", error=str(e))
        except Exception as e:
            logger.error("ocr_extract_error", error=str(e), file=file_path)

        self.last_confidence = 0.4 if records else 0.0
        logger.info("ocr_parser_extracted", count=len(records))
        return records

    def _parse_text(self, text: str, page_num: int) -> list[ExtractedRecord]:
        """
        Heuristic text parsing: look for lines containing register numbers.
        This is a best-effort extraction; confidence is low.
        Low-confidence records are flagged for human review.
        """
        records: list[ExtractedRecord] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            reg_match = REGISTER_PATTERN.search(line)
            if not reg_match:
                continue

            marks = MARKS_PATTERN.findall(line)
            total = marks[-1] if marks else None
            absent = total and total.upper() in ("AB", "ABS")

            records.append(ExtractedRecord(
                raw_register_number=reg_match.group(),
                raw_total_marks=total if not absent else None,
                is_absent=bool(absent),
                page_number=page_num,
                extraction_method="ocr",
                confidence_score=0.40,  # all OCR records are low-confidence
                line_reference=line[:200],
            ))
        return records
