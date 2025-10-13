"""
Parser for detecting stay restrictions in onsen remarks.

This parser checks if an onsen is restricted to guests staying at the facility
by looking for "宿泊限定" (stay-limited) in the remarks column.
"""

from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class StayRestrictionParsed:
    """Parsed stay restriction information."""

    raw: Optional[str]
    normalized: Optional[str]
    is_stay_restricted: bool
    requires_inquiry: bool
    notes: list[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


def parse_stay_restriction(value: Optional[str | Any]) -> StayRestrictionParsed:
    """
    Parse stay restriction information from onsen remarks.

    Args:
        value: The raw remarks text from the onsen

    Returns:
        StayRestrictionParsed object with parsed information
    """
    if not value:
        return StayRestrictionParsed(
            raw=value,
            normalized=None if value is None else "",
            is_stay_restricted=False,
            requires_inquiry=False,
        )

    # Ensure value is a string
    if not isinstance(value, str):
        return StayRestrictionParsed(
            raw=value, normalized=None, is_stay_restricted=False, requires_inquiry=False
        )

    # Normalize the text for consistent matching
    normalized = _normalize_text(value)

    # Check for stay restriction indicators
    is_stay_restricted = _detect_stay_restriction(normalized)

    # Check if inquiry is required (ambiguous cases)
    requires_inquiry = _requires_inquiry(normalized)

    # Extract relevant notes
    notes = _extract_notes(normalized, is_stay_restricted)

    return StayRestrictionParsed(
        raw=value,
        normalized=normalized,
        is_stay_restricted=is_stay_restricted,
        requires_inquiry=requires_inquiry,
        notes=notes,
    )


def _normalize_text(text: str) -> str:
    """Normalize text for consistent matching."""
    if not isinstance(text, str):
        return ""

    # Convert to lowercase and remove extra whitespace
    normalized = text.lower().strip()
    # Replace multiple spaces with single space
    normalized = " ".join(normalized.split())
    return normalized


def _detect_stay_restriction(normalized_text: str) -> bool:
    """
    Detect if the onsen is stay-restricted.

    Looks for patterns like:
    - 宿泊限定 (stay-limited)
    - 宿泊者限定 (limited to guests)
    - 宿泊客限定 (limited to guests)
    - 宿泊者のみ (guests only)
    - 宿泊客のみ (guests only)
    """
    stay_restriction_patterns = [
        "宿泊限定",
        "宿泊者限定",
        "宿泊客限定",
        "宿泊者のみ",
        "宿泊客のみ",
        "宿泊者専用",
        "宿泊客専用",
        "宿泊者向け",
        "宿泊客向け",
    ]

    # Remove spaces from normalized text for exact pattern matching
    text_for_matching = normalized_text.replace(" ", "")

    return any(pattern in text_for_matching for pattern in stay_restriction_patterns)


def _requires_inquiry(normalized_text: str) -> bool:
    """
    Check if the stay restriction status requires inquiry.

    Looks for ambiguous patterns that might need clarification.
    """
    ambiguous_patterns = [
        "要確認",
        "要問合せ",
        "要相談",
        "要予約",
        "事前確認",
        "事前問合せ",
        "事前相談",
    ]

    return any(pattern in normalized_text for pattern in ambiguous_patterns)


def _extract_notes(normalized_text: str, is_stay_restricted: bool) -> list[str]:
    """Extract relevant notes about stay restrictions."""
    notes = []

    if is_stay_restricted:
        notes.append("Stay-restricted onsen (宿泊限定)")

        # Check for additional context
        if "宿泊者限定" in normalized_text:
            notes.append("Limited to facility guests only")
        elif "宿泊客限定" in normalized_text:
            notes.append("Limited to facility guests only")
        elif "宿泊者のみ" in normalized_text:
            notes.append("Guests only")
        elif "宿泊客のみ" in normalized_text:
            notes.append("Guests only")

    # Check for exceptions or special conditions
    if "日帰り" in normalized_text and is_stay_restricted:
        notes.append("Day-trip access may be available (日帰り)")

    if "要確認" in normalized_text:
        notes.append("Confirmation required (要確認)")

    if "要予約" in normalized_text:
        notes.append("Reservation required (要予約)")

    return notes
