"""
Parser registry: selects the best parser for a given PDF.
Chain: UniversitySpecificParsers (by confidence) → GenericPDFParser → OCRParser
"""
from __future__ import annotations

import structlog

from app.parsers.base import BaseParser, ResultParser
from app.parsers.generic_pdf import GenericPDFParser
from app.parsers.ocr_parser import OCRParser

logger = structlog.get_logger(__name__)

MIN_CONFIDENCE_THRESHOLD = 0.5


class ParserRegistry:
    """
    Holds all registered parsers. University-specific parsers are registered
    via the plugin mechanism. Generic and OCR are always available.
    """

    def __init__(self) -> None:
        self._specific_parsers: list[ResultParser] = []
        self._generic = GenericPDFParser()
        self._ocr = OCRParser()
        self._load_plugins()

    def _load_plugins(self) -> None:
        """Dynamically load university-specific parser plugins."""
        try:
            from app.parsers.plugins import PLUGIN_PARSERS
            self._specific_parsers = list(PLUGIN_PARSERS)
            logger.info("parsers_loaded", plugins=[p.name for p in self._specific_parsers])
        except ImportError:
            logger.info("no_parser_plugins_found")

    def register(self, parser: ResultParser) -> None:
        self._specific_parsers.append(parser)

    def select_parser(self, file_path: str) -> ResultParser:
        """
        Select the best parser for a given PDF file.
        Returns the highest-confidence parser above the threshold,
        falling back to Generic → OCR.
        """
        best_parser: ResultParser | None = None
        best_confidence = 0.0

        for parser in self._specific_parsers:
            can, conf = parser.can_parse(file_path)
            logger.debug("parser_check", parser=parser.name, can=can, confidence=conf)
            if can and conf > best_confidence:
                best_confidence = conf
                best_parser = parser

        if best_parser and best_confidence >= MIN_CONFIDENCE_THRESHOLD:
            logger.info("parser_selected", parser=best_parser.name, confidence=best_confidence)
            return best_parser

        # Try generic
        can, conf = self._generic.can_parse(file_path)
        if can and conf >= MIN_CONFIDENCE_THRESHOLD:
            logger.info("parser_selected", parser="GenericPDFParser", confidence=conf)
            return self._generic

        # Fall back to OCR
        logger.info("parser_selected", parser="OCRParser", reason="fallback")
        return self._ocr
