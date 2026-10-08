# ADR-005: OCR Library — Tesseract (default), PaddleOCR (upgrade path)

**Date:** 2026-10-07  
**Status:** Accepted — pending benchmark on real PDFs  
**Alternatives considered:** PaddleOCR, AWS Textract, Azure Form Recognizer, EasyOCR

## Context

Some university result PDFs are scanned image-based documents. We need OCR fallback for the parser chain.

## Decision

- **Default:** `pytesseract` (Python binding for Tesseract 5.x).
- **Upgrade path:** PaddleOCR — if Tesseract character accuracy on real samples falls below 95%, switch to PaddleOCR.
- Cloud OCR services (Textract, Form Recognizer) are explicitly deferred: they would send student data to external APIs, raising privacy concerns under the DPDP Act 2023.

## Benchmark requirement

Before claiming H1 accuracy (≥98%), run OCR on actual sample PDFs and report:
1. Character Error Rate (CER) per page
2. Field-level exact-match rate
3. False-match rate for register numbers

Document results in `docs/evaluation/ocr-benchmark.md`.

## Consequences

- `app/parsers/ocr_parser.py` uses `pytesseract`. All OCR records have `confidence_score ≤ 0.40` and are flagged for human review.
- OCR is the last resort in the parser chain; it is only invoked when `GenericPDFParser` confidence < 0.5.
- The Dockerfile installs `tesseract-ocr` and `tesseract-ocr-eng` system packages.
