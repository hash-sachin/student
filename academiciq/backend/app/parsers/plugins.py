"""
University-specific parser plugins.
Add new parsers here as subclasses of BaseParser.
Each plugin is auto-discovered by the ParserRegistry.

IMPORTANT: Parsers must be validated against real sample PDFs (Section 5.1 of spec).
           The GenericPDFParser and SyntheticParser are for testing only.
           Real university parsers require actual sample PDFs in tests/golden/.
"""
from __future__ import annotations

from app.parsers.synthetic import SyntheticParser

# List of registered plugin parsers (highest-confidence tried first)
PLUGIN_PARSERS = [
    SyntheticParser(),
    # Add university-specific parsers here:
    # AnnaUniversityParser(),
    # VTUParser(),
    # etc.
]
