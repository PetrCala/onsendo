"""
Distance calculation utilities for onsen recommendations.
"""

import math
from typing import Tuple, List, Optional
from dataclasses import dataclass
from src.db.models import Onsen, Location


@dataclass
class DistanceCategory:
    """Distance categories for filtering recommendations."""

    name: str
    max_distance_km: float
    description: str


# Predefined distance categories
DISTANCE_CATEGORIES = {
    "very_close": DistanceCategory("very_close", 5.0, "Very close (within 5km)"),
    "close": DistanceCategory("close", 15.0, "Close (within 15km)"),
    "medium": DistanceCategory("medium", 50.0, "Medium distance (within 50km)"),
    "far": DistanceCategory("far", float("inf"), "Far (any distance)"),
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Args:
        lat1, lon1: Latitude and longitude of first point in degrees
        lat2, lon2: Latitude and longitude of second point in degrees

    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in kilometers
    r = 6371

    return c * r


def calculate_distance_to_onsen(location: Location, onsen: Onsen) -> Optional[float]:
    """
    Calculate distance between a location and an onsen.

    Args:
        location: Location object with coordinates
        onsen: Onsen object with coordinates

    Returns:
        Distance in kilometers, or None if coordinates are missing
    """
    if (
        location.latitude is None
        or location.longitude is None
        or onsen.latitude is None
        or onsen.longitude is None
    ):
        return None

    return haversine_distance(
        location.latitude, location.longitude, onsen.latitude, onsen.longitude
    )


def filter_onsens_by_distance(
    onsens: List[Onsen], location: Location, distance_category: str
) -> List[Tuple[Onsen, float]]:
    """
    Filter onsens by distance from a location.

    Args:
        onsens: List of onsen objects
        location: Location object with coordinates
        distance_category: Distance category key (very_close, close, medium, far)

    Returns:
        List of tuples (onsen, distance_km) within the specified distance
    """
    if distance_category not in DISTANCE_CATEGORIES:
        raise ValueError(f"Invalid distance category: {distance_category}")

    category = DISTANCE_CATEGORIES[distance_category]
    filtered_onsens = []

    for onsen in onsens:
        distance = calculate_distance_to_onsen(location, onsen)
        if distance is not None and distance <= category.max_distance_km:
            filtered_onsens.append((onsen, distance))

    # Sort by distance (closest first)
    filtered_onsens.sort(key=lambda x: x[1])
    return filtered_onsens


def get_distance_category_name(distance_km: float) -> str:
    """
    Get the name of the distance category for a given distance.

    Args:
        distance_km: Distance in kilometers

    Returns:
        Distance category name
    """
    for category_key, category in DISTANCE_CATEGORIES.items():
        if distance_km <= category.max_distance_km:
            return category_key
    return "far"
