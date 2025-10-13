"""Onsen identification utilities for finding onsens based on various criteria."""

import math
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import Onsen
from src.lib.distance import haversine_distance


@dataclass
class OnsenMatch:
    """Represents a matched onsen with confidence score."""

    onsen: Onsen
    confidence: float
    match_type: str
    match_details: str


def _calculate_string_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity between two strings using SequenceMatcher.

    Args:
        str1: First string
        str2: Second string

    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not str1 or not str2:
        return 0.0

    # Normalize strings for comparison
    str1_norm = str1.lower().strip()
    str2_norm = str2.lower().strip()

    # Exact match
    if str1_norm == str2_norm:
        return 1.0

    # Calculate similarity ratio
    return SequenceMatcher(None, str1_norm, str2_norm).ratio()


def identify_by_name(
    db_session: Session, name: str, threshold: float = 0.6, limit: int = 5
) -> list[OnsenMatch]:
    """
    Identify onsens by name using fuzzy matching.

    Args:
        db_session: Database session
        name: Name to search for
        threshold: Minimum similarity threshold (0.0-1.0)
        limit: Maximum number of results to return

    Returns:
        List of OnsenMatch objects sorted by confidence (highest first)
    """
    all_onsens = db_session.query(Onsen).all()
    matches: list[OnsenMatch] = []

    for onsen in all_onsens:
        if not onsen.name:
            continue

        similarity = _calculate_string_similarity(name, onsen.name)

        if similarity >= threshold:
            match = OnsenMatch(
                onsen=onsen,
                confidence=similarity,
                match_type="name",
                match_details=f"Name similarity: {similarity:.2%}",
            )
            matches.append(match)

    # Sort by confidence (highest first) and limit results
    matches.sort(key=lambda x: x.confidence, reverse=True)
    return matches[:limit]


def identify_by_coordinates(
    db_session: Session,
    latitude: float,
    longitude: float,
    max_distance_km: Optional[float] = None,
    limit: int = 5,
) -> list[OnsenMatch]:
    """
    Identify onsens by geographical proximity.

    Args:
        db_session: Database session
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        max_distance_km: Maximum distance in kilometers (None for no limit)
        limit: Maximum number of results to return

    Returns:
        List of OnsenMatch objects sorted by distance (closest first)
    """
    all_onsens = db_session.query(Onsen).all()
    matches: list[tuple[OnsenMatch, float]] = []

    for onsen in all_onsens:
        if onsen.latitude is None or onsen.longitude is None:
            continue

        distance = haversine_distance(latitude, longitude, onsen.latitude, onsen.longitude)

        # Skip if beyond max distance
        if max_distance_km is not None and distance > max_distance_km:
            continue

        # Calculate confidence based on distance (closer = higher confidence)
        # Using exponential decay: confidence = e^(-distance/scale)
        # Scale of 1.0 km means ~37% confidence at 1km, ~14% at 2km
        confidence = math.exp(-distance / 1.0)

        match = OnsenMatch(
            onsen=onsen,
            confidence=confidence,
            match_type="location",
            match_details=f"Distance: {distance:.2f} km",
        )
        matches.append((match, distance))

    # Sort by distance (closest first) and limit results
    matches.sort(key=lambda x: x[1])
    return [match for match, _ in matches[:limit]]


def identify_by_address(
    db_session: Session, address: str, threshold: float = 0.5, limit: int = 5
) -> list[OnsenMatch]:
    """
    Identify onsens by address using fuzzy matching.

    Args:
        db_session: Database session
        address: Address to search for
        threshold: Minimum similarity threshold (0.0-1.0)
        limit: Maximum number of results to return

    Returns:
        List of OnsenMatch objects sorted by confidence (highest first)
    """
    all_onsens = db_session.query(Onsen).all()
    matches: list[OnsenMatch] = []

    for onsen in all_onsens:
        if not onsen.address:
            continue

        similarity = _calculate_string_similarity(address, onsen.address)

        if similarity >= threshold:
            match = OnsenMatch(
                onsen=onsen,
                confidence=similarity,
                match_type="address",
                match_details=f"Address similarity: {similarity:.2%}",
            )
            matches.append(match)

    # Sort by confidence (highest first) and limit results
    matches.sort(key=lambda x: x.confidence, reverse=True)
    return matches[:limit]


def identify_by_region(
    db_session: Session, region: str, threshold: float = 0.6, limit: int = 10
) -> list[OnsenMatch]:
    """
    Identify onsens by region using fuzzy matching.

    Args:
        db_session: Database session
        region: Region name to search for
        threshold: Minimum similarity threshold (0.0-1.0)
        limit: Maximum number of results to return

    Returns:
        List of OnsenMatch objects sorted by confidence (highest first)
    """
    all_onsens = db_session.query(Onsen).all()
    matches: list[OnsenMatch] = []

    for onsen in all_onsens:
        if not onsen.region:
            continue

        similarity = _calculate_string_similarity(region, onsen.region)

        if similarity >= threshold:
            match = OnsenMatch(
                onsen=onsen,
                confidence=similarity,
                match_type="region",
                match_details=f"Region similarity: {similarity:.2%}",
            )
            matches.append(match)

    # Sort by confidence (highest first) and limit results
    matches.sort(key=lambda x: x.confidence, reverse=True)
    return matches[:limit]


def identify_onsen(
    db_session: Session,
    name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    address: Optional[str] = None,
    region: Optional[str] = None,
    max_distance_km: Optional[float] = None,
    name_threshold: float = 0.6,
    address_threshold: float = 0.5,
    region_threshold: float = 0.6,
    limit: int = 5,
) -> list[OnsenMatch]:
    """
    Identify onsens using multiple criteria.

    This function combines results from different identification methods
    and returns the most confident matches.

    Args:
        db_session: Database session
        name: Onsen name to search for
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        address: Address to search for
        region: Region to search for
        max_distance_km: Maximum distance for location-based search
        name_threshold: Minimum similarity threshold for name matching
        address_threshold: Minimum similarity threshold for address matching
        region_threshold: Minimum similarity threshold for region matching
        limit: Maximum number of results to return

    Returns:
        List of OnsenMatch objects sorted by confidence (highest first)
    """
    all_matches: list[OnsenMatch] = []

    # Collect matches from all available criteria
    if name:
        all_matches.extend(identify_by_name(db_session, name, name_threshold, limit * 2))

    if latitude is not None and longitude is not None:
        all_matches.extend(
            identify_by_coordinates(
                db_session, latitude, longitude, max_distance_km, limit * 2
            )
        )

    if address:
        all_matches.extend(
            identify_by_address(db_session, address, address_threshold, limit * 2)
        )

    if region:
        all_matches.extend(
            identify_by_region(db_session, region, region_threshold, limit * 2)
        )

    if not all_matches:
        return []

    # Consolidate matches: combine scores for the same onsen
    onsen_scores: dict[int, tuple[OnsenMatch, float]] = {}

    for match in all_matches:
        onsen_id = match.onsen.id
        if onsen_id in onsen_scores:
            # Average the confidence scores for the same onsen
            existing_match, existing_score = onsen_scores[onsen_id]
            new_score = (existing_score + match.confidence) / 2
            # Combine match details
            combined_details = f"{existing_match.match_details}; {match.match_details}"
            combined_match = OnsenMatch(
                onsen=match.onsen,
                confidence=new_score,
                match_type="combined",
                match_details=combined_details,
            )
            onsen_scores[onsen_id] = (combined_match, new_score)
        else:
            onsen_scores[onsen_id] = (match, match.confidence)

    # Extract matches and sort by confidence
    consolidated_matches = [match for match, _ in onsen_scores.values()]
    consolidated_matches.sort(key=lambda x: x.confidence, reverse=True)

    return consolidated_matches[:limit]
