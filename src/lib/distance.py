"""
Distance calculation utilities for onsen recommendations.
"""

import math
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
from statistics import mean, median, stdev
from src.db.models import Onsen, Location


@dataclass
class DistanceCategory:
    """Distance categories for filtering recommendations."""

    name: str
    max_distance_km: float
    description: str


@dataclass
class DistanceMilestones:
    """Distance milestones calculated from onsen distribution."""

    very_close_max: float
    close_max: float
    medium_max: float
    far_min: float

    def to_categories(self) -> Dict[str, DistanceCategory]:
        """Convert milestones to distance categories."""
        return {
            "very_close": DistanceCategory(
                "very_close",
                self.very_close_max,
                f"Very close (within {self.very_close_max:.1f}km)",
            ),
            "close": DistanceCategory(
                "close", self.close_max, f"Close (within {self.close_max:.1f}km)"
            ),
            "medium": DistanceCategory(
                "medium",
                self.medium_max,
                f"Medium distance (within {self.medium_max:.1f}km)",
            ),
            "far": DistanceCategory(
                "far", float("inf"), f"Far (beyond {self.medium_max:.1f}km)"
            ),
        }


def calculate_distance_milestones(location: Location, db_session) -> DistanceMilestones:
    """
    Calculate distance milestones for a location based on the distribution of onsen distances.

    Args:
        location: Location to calculate milestones for
        db_session: Database session to query onsens

    Returns:
        DistanceMilestones object with calculated thresholds
    """
    # Get all onsens
    onsens = db_session.query(Onsen).all()
    if not onsens:
        # Return default milestones if no onsens found
        return DistanceMilestones(5.0, 15.0, 50.0, 50.0)

    # Calculate distances
    distances = []
    for onsen in onsens:
        distance = calculate_distance_to_onsen(location, onsen)
        if distance is not None:
            distances.append(distance)

    if not distances:
        # Return default milestones if no valid distances
        return DistanceMilestones(5.0, 15.0, 50.0, 50.0)

    # Sort distances for percentile calculation
    sorted_distances = sorted(distances)
    n = len(sorted_distances)

    # Helper function to calculate quantiles
    def quantile(data: List[float], q: float) -> float:
        """Calculate quantile value from sorted data."""
        idx = int(q * (len(data) - 1))
        return data[idx]

    # Calculate milestones using quantiles
    very_close_max = quantile(sorted_distances, 0.20)  # 20th percentile
    close_max = quantile(sorted_distances, 0.50)  # 50th percentile (median)
    medium_max = quantile(sorted_distances, 0.80)  # 80th percentile

    return DistanceMilestones(
        very_close_max=very_close_max,
        close_max=close_max,
        medium_max=medium_max,
        far_min=medium_max,
    )


# Predefined distance categories (fallback)
DEFAULT_DISTANCE_CATEGORIES = {
    "very_close": DistanceCategory("very_close", 5.0, "Very close (within 5km)"),
    "close": DistanceCategory("close", 15.0, "Close (within 15km)"),
    "medium": DistanceCategory("medium", 50.0, "Medium distance (within 50km)"),
    "far": DistanceCategory("far", float("inf"), "Far (any distance)"),
}

# Global variable to hold dynamic categories
DISTANCE_CATEGORIES = DEFAULT_DISTANCE_CATEGORIES.copy()


def update_distance_categories(milestones: DistanceMilestones) -> None:
    """Update the global distance categories with new milestones."""
    global DISTANCE_CATEGORIES
    DISTANCE_CATEGORIES = milestones.to_categories()


def reset_distance_categories() -> None:
    """Reset distance categories to default values."""
    global DISTANCE_CATEGORIES
    DISTANCE_CATEGORIES = DEFAULT_DISTANCE_CATEGORIES.copy()


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
