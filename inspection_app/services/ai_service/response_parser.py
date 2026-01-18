"""
Parse AI responses into structured data.
"""

import re
from typing import Optional
from dataclasses import dataclass
from core.inspection_item import MatchType, ConfidenceLevel


@dataclass
class AIAnalysisResult:
    """Structured result from AI analysis."""
    match_type: Optional[MatchType] = None
    reference: str = ""
    confidence: Optional[ConfidenceLevel] = None
    reasoning: str = ""
    is_valid: bool = False
    raw_response: str = ""


def parse_analysis_response(response_text: str) -> AIAnalysisResult:
    """Parse AI response text into structured result."""
    result = AIAnalysisResult(raw_response=response_text)

    # Extract MATCH_TYPE
    match_type_match = re.search(
        r'MATCH_TYPE:\s*(Section|Table|Figure)',
        response_text,
        re.IGNORECASE
    )
    if match_type_match:
        type_str = match_type_match.group(1).capitalize()
        try:
            result.match_type = MatchType(type_str)
        except ValueError:
            pass

    # Extract REFERENCE
    ref_match = re.search(
        r'REFERENCE:\s*(.+?)(?:\n|$)',
        response_text,
        re.IGNORECASE
    )
    if ref_match:
        result.reference = ref_match.group(1).strip()

    # Extract CONFIDENCE
    conf_match = re.search(
        r'CONFIDENCE:\s*(High|Medium|Low)',
        response_text,
        re.IGNORECASE
    )
    if conf_match:
        conf_str = conf_match.group(1).capitalize()
        try:
            result.confidence = ConfidenceLevel(conf_str)
        except ValueError:
            pass

    # Extract REASONING
    reason_match = re.search(
        r'REASONING:\s*(.+?)(?:\n\n|$)',
        response_text,
        re.IGNORECASE | re.DOTALL
    )
    if reason_match:
        result.reasoning = reason_match.group(1).strip()

    # Check validity
    result.is_valid = bool(
        result.match_type and
        result.reference and
        result.confidence
    )

    return result


def extract_search_term(reference: str, match_type: Optional[MatchType]) -> str:
    """Extract searchable term from reference."""
    if not reference:
        return ""

    # Clean up the reference
    term = reference.strip()

    # For tables and figures, might need to add prefix
    if match_type == MatchType.TABLE and not term.lower().startswith('table'):
        term = f"Table {term}"
    elif match_type == MatchType.FIGURE and not term.lower().startswith('figure'):
        term = f"Figure {term}"

    return term
