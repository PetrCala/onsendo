"""Onsen filtering utilities for keyword-based searches."""

from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import Onsen


def filter_onsens_by_keyword(
    db: Session,
    keywords: list[str],
    fields: Optional[list[str]] = None
) -> list[Onsen]:
    """
    Filter onsens by keyword search across specified fields.

    Args:
        db: Database session
        keywords: List of keywords to search for (OR logic - match any)
        fields: List of field names to search in. Options:
               - ['name'] (default)
               - ['name', 'description', 'business_form', 'remarks']
               - ['all'] (searches all text fields)
               If None, defaults to ['name']

    Returns:
        List of Onsen objects matching any of the keywords in any of the fields

    Examples:
        >>> # Search for foot baths in name field
        >>> filter_onsens_by_keyword(db, ["足湯"])
        >>> # Search for multiple keywords in all fields
        >>> filter_onsens_by_keyword(db, ["足湯", "温泉"], fields=["all"])
    """
    # Default to searching name field only
    if fields is None:
        fields = ["name"]

    # Expand 'all' to all searchable text fields
    if "all" in fields:
        fields = ["name", "description", "business_form", "remarks", "address", "region"]

    # Get all onsens
    all_onsens = db.query(Onsen).all()

    # Filter onsens by keywords
    matching_onsens = []
    for onsen in all_onsens:
        if _matches_any_keyword(onsen, keywords, fields):
            matching_onsens.append(onsen)

    return matching_onsens


def _matches_any_keyword(onsen: Onsen, keywords: list[str], fields: list[str]) -> bool:
    """
    Check if an onsen matches any of the keywords in any of the specified fields.

    Args:
        onsen: Onsen object to check
        keywords: List of keywords to search for
        fields: List of field names to search in

    Returns:
        True if any keyword matches in any field, False otherwise
    """
    # Normalize keywords to lowercase for case-insensitive search
    normalized_keywords = [kw.lower() for kw in keywords]

    # Check each field
    for field_name in fields:
        field_value = getattr(onsen, field_name, None)

        # Skip None values
        if field_value is None:
            continue

        # Convert to string and normalize
        field_text = str(field_value).lower()

        # Check if any keyword matches (substring search)
        for keyword in normalized_keywords:
            if keyword in field_text:
                return True

    return False


def format_onsen_summary_table(onsens: list[Onsen]) -> str:
    """
    Format a list of onsens into a readable table for CLI display.

    Args:
        onsens: List of Onsen objects to format

    Returns:
        Formatted string table with onsen details
    """
    if not onsens:
        return "No onsens found."

    # Build header
    header = (
        f"{'Ban#':<6} {'Name':<40} {'Region':<15} "
        f"{'Coordinates':<25} {'Fee':<15} {'Hours':<20}"
    )
    separator = "-" * len(header)

    # Build rows
    rows = []
    for onsen in onsens:
        ban = onsen.ban_number or "N/A"
        name = (onsen.name[:37] + "...") if len(onsen.name) > 40 else onsen.name
        region = (onsen.region[:12] + "...") if onsen.region and len(onsen.region) > 15 else (onsen.region or "N/A")
        coords = f"{onsen.latitude:.4f}, {onsen.longitude:.4f}" if onsen.latitude and onsen.longitude else "N/A"
        fee = (onsen.admission_fee[:12] + "...") if onsen.admission_fee and len(onsen.admission_fee) > 15 else (onsen.admission_fee or "N/A")
        hours = (onsen.usage_time[:17] + "...") if onsen.usage_time and len(onsen.usage_time) > 20 else (onsen.usage_time or "N/A")

        row = f"{ban:<6} {name:<40} {region:<15} {coords:<25} {fee:<15} {hours:<20}"
        rows.append(row)

    # Combine
    table = "\n".join([separator, header, separator] + rows + [separator])
    return table
