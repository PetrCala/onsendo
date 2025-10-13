"""Distance calculation utilities for onsen recommendations."""

import heapq
import math
from typing import Optional
from dataclasses import dataclass
from statistics import mean, median, stdev

from src.db.models import Onsen, Location
from src.lib.cache import (
    CacheNamespace,
    encode_cache_key,
    get_recommendation_cache,
)


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

    def to_categories(self) -> dict[str, DistanceCategory]:
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
            "any": DistanceCategory(
                "any", float("inf"), "Any distance"
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
    def quantile(data: list[float], q: float) -> float:
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
    "any": DistanceCategory("any", float("inf"), "Any distance"),
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

    cache = get_recommendation_cache()
    cache_key = encode_cache_key(
        "distance",
        getattr(location, "id", None) or getattr(location, "name", "custom"),
        f"{location.latitude:.6f}",
        f"{location.longitude:.6f}",
        getattr(onsen, "id", None),
        f"{onsen.latitude:.6f}",
        f"{onsen.longitude:.6f}",
    )

    cached_value = cache.get(CacheNamespace.DISTANCE, cache_key)
    if cached_value is not None:
        return cached_value

    distance = haversine_distance(
        location.latitude, location.longitude, onsen.latitude, onsen.longitude
    )

    cache.set(CacheNamespace.DISTANCE, cache_key, distance, ttl_seconds=24 * 60 * 60)
    return distance


def filter_onsens_by_distance(
    onsens: list[Onsen],
    location: Location,
    distance_category: str,
    limit: Optional[int] = None,
) -> list[tuple[Onsen, float]]:
    """
    Filter onsens by distance from a location.

    Args:
        onsens: List of onsen objects
        location: Location object with coordinates
        distance_category: Distance category key (very_close, close, medium, far)

    Returns:
        List of tuples (onsen, distance_km) within the specified distance category
    """
    if distance_category not in DISTANCE_CATEGORIES:
        raise ValueError(f"Invalid distance category: {distance_category}")

    if limit is not None and limit <= 0:
        return []

    filtered_onsens: list[tuple[Onsen, float]] = []
    use_heap = limit is not None
    heap: list[tuple[float, int, Onsen, float]] = []
    counter = 0

    for onsen in onsens:
        distance = calculate_distance_to_onsen(location, onsen)
        if distance is None:
            continue

        # Check if the onsen falls within the requested distance category
        if _is_distance_in_category(distance, distance_category):
            if use_heap:
                if len(heap) < (limit or 0):
                    counter += 1
                    heapq.heappush(heap, (-distance, counter, onsen, distance))
                else:
                    if heap and distance < -heap[0][0]:
                        counter += 1
                        heapq.heapreplace(heap, (-distance, counter, onsen, distance))
            else:
                filtered_onsens.append((onsen, distance))

    if use_heap:
        # Convert the heap into a sorted list of (onsen, distance) pairs
        filtered_onsens = [
            (onsen, dist) for _, _, onsen, dist in sorted(heap, key=lambda item: item[3])
        ]
    else:
        # Sort by distance (closest first)
        filtered_onsens.sort(key=lambda x: x[1])

    return filtered_onsens


def _is_distance_in_category(distance_km: float, category: str) -> bool:
    """
    Check if a distance falls within a specific distance category.

    Args:
        distance_km: Distance in kilometers
        category: Distance category (very_close, close, medium, far, any)

    Returns:
        True if distance is within the category, False otherwise
    """
    if category == "any":
        return True
    elif category == "very_close":
        return distance_km <= DISTANCE_CATEGORIES["very_close"].max_distance_km
    elif category == "close":
        return (
            distance_km > DISTANCE_CATEGORIES["very_close"].max_distance_km
            and distance_km <= DISTANCE_CATEGORIES["close"].max_distance_km
        )
    elif category == "medium":
        return (
            distance_km > DISTANCE_CATEGORIES["close"].max_distance_km
            and distance_km <= DISTANCE_CATEGORIES["medium"].max_distance_km
        )
    elif category == "far":
        return distance_km > DISTANCE_CATEGORIES["medium"].max_distance_km
    else:
        return False


def get_distance_category_name(distance_km: float) -> str:
    """
    Get the name of the distance category for a given distance.

    Args:
        distance_km: Distance in kilometers

    Returns:
        Distance category name
    """
    if distance_km <= DISTANCE_CATEGORIES["very_close"].max_distance_km:
        return "very_close"
    elif distance_km <= DISTANCE_CATEGORIES["close"].max_distance_km:
        return "close"
    elif distance_km <= DISTANCE_CATEGORIES["medium"].max_distance_km:
        return "medium"
    else:
        return "far"
