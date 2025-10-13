"""
Distance milestone calculation utilities.
"""

from typing import Optional
from statistics import mean, median, stdev
from sqlalchemy.orm import Session

from src.db.models import Onsen, Location
from src.lib.cache import (
    CacheNamespace,
    encode_cache_key,
    get_recommendation_cache,
)
from src.lib.distance import calculate_distance_to_onsen, DistanceMilestones


def calculate_location_milestones(
    location: Location, db_session: Session
) -> DistanceMilestones:
    """
    Calculate distance milestones for a location based on the distribution of onsen distances.

    This function analyzes all onsens in the database and calculates four distance thresholds
    based on the distribution of distances from the given location:
    - very_close_max: 20th percentile (closest 20% of onsens)
    - close_max: 50th percentile (median distance)
    - medium_max: 80th percentile (80% of onsens within this distance)
    - far_min: same as medium_max (anything beyond medium_max is considered far)

    Args:
        location: Location to calculate milestones for
        db_session: Database session to query onsens

    Returns:
        DistanceMilestones object with calculated thresholds

    Raises:
        ValueError: If no onsens found or no valid distances calculated
    """
    cache = get_recommendation_cache()
    cache_key = encode_cache_key(
        "milestones",
        getattr(location, "id", None) or getattr(location, "name", "custom"),
        f"{location.latitude:.6f}",
        f"{location.longitude:.6f}",
    )

    cached_value = cache.get(CacheNamespace.MILESTONES, cache_key)
    if cached_value is not None:
        return DistanceMilestones(**cached_value)

    # Get all onsens
    onsens = db_session.query(Onsen).all()
    if not onsens:
        raise ValueError("No onsens found in the database")

    # Calculate distances
    distances = []
    onsen_distances = []

    for onsen in onsens:
        try:
            distance = calculate_distance_to_onsen(location, onsen)
            if distance is not None:
                distances.append(distance)
                onsen_distances.append((onsen, distance))
        except Exception as e:
            print(f"Warning: Error calculating distance for onsen {onsen.id}: {e}")
            continue

    if not distances:
        raise ValueError("No valid distances could be calculated for any onsens")

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

    milestones = DistanceMilestones(
        very_close_max=very_close_max,
        close_max=close_max,
        medium_max=medium_max,
        far_min=medium_max,
    )

    cache.set(
        CacheNamespace.MILESTONES,
        cache_key,
        {
            "very_close_max": milestones.very_close_max,
            "close_max": milestones.close_max,
            "medium_max": milestones.medium_max,
            "far_min": milestones.far_min,
        },
        ttl_seconds=12 * 60 * 60,
    )

    return milestones


def analyze_location_distances(location: Location, db_session: Session) -> dict:
    """
    Analyze distance distribution for a location and return detailed statistics.

    Args:
        location: Location to analyze
        db_session: Database session to query onsens

    Returns:
        Dictionary containing analysis results including milestones and statistics
    """
    # Get all onsens
    onsens = db_session.query(Onsen).all()
    if not onsens:
        return {"error": "No onsens found in the database"}

    # Calculate distances
    distances = []
    onsen_distances = []

    for onsen in onsens:
        try:
            distance = calculate_distance_to_onsen(location, onsen)
            if distance is not None:
                distances.append(distance)
                onsen_distances.append((onsen, distance))
        except Exception as e:
            print(f"Warning: Error calculating distance for onsen {onsen.id}: {e}")
            continue

    if not distances:
        return {"error": "No valid distances could be calculated"}

    # Calculate statistics
    sorted_distances = sorted(distances)
    n = len(sorted_distances)

    def quantile(data: list[float], q: float) -> float:
        idx = int(q * (len(data) - 1))
        return data[idx]

    # Calculate milestones
    very_close_max = quantile(sorted_distances, 0.20)
    close_max = quantile(sorted_distances, 0.50)
    medium_max = quantile(sorted_distances, 0.80)

    # Calculate statistics
    stats = {
        "mean": mean(distances),
        "median": median(distances),
        "min": min(distances),
        "max": max(distances),
        "count": len(distances),
    }

    if len(distances) > 1:
        stats["stddev"] = stdev(distances)
    else:
        stats["stddev"] = None

    # Create milestones object
    milestones = DistanceMilestones(
        very_close_max=very_close_max,
        close_max=close_max,
        medium_max=medium_max,
        far_min=medium_max,
    )

    return {
        "location": {
            "name": location.name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        },
        "milestones": milestones,
        "statistics": stats,
        "onsen_count": len(onsen_distances),
        "sample_distances": onsen_distances[:10],  # First 10 for reference
    }


def print_milestone_analysis(analysis: dict) -> None:
    """
    Print a formatted analysis of distance milestones.

    Args:
        analysis: Analysis result from analyze_location_distances
    """
    if "error" in analysis:
        print(f"Error: {analysis['error']}")
        return

    location = analysis["location"]
    milestones = analysis["milestones"]
    stats = analysis["statistics"]

    print(
        f"Reference location: {location['name']} (lat={location['latitude']}, lon={location['longitude']})"
    )
    print(f"Analyzed distances for {analysis['onsen_count']} onsens.\n")

    print("--- Distance Statistics ---")
    print(f"Mean:   {stats['mean']:.2f} km")
    print(f"Median: {stats['median']:.2f} km")
    print(f"Min:    {stats['min']:.2f} km")
    print(f"Max:    {stats['max']:.2f} km")
    if stats["stddev"] is not None:
        print(f"Stddev: {stats['stddev']:.2f} km")
    else:
        print("Stddev: N/A (only one onsen)")

    print("\n--- Calculated Distance Milestones ---")
    print(f"very_close: <= {milestones.very_close_max:.2f} km")
    print(f"close:      <= {milestones.close_max:.2f} km")
    print(f"medium:     <= {milestones.medium_max:.2f} km")
    print(f"far:        >  {milestones.medium_max:.2f} km")

    if analysis["sample_distances"]:
        print("\n--- Sample Distances ---")
        for onsen, dist in analysis["sample_distances"]:
            print(f"  {onsen.name} (ID: {onsen.id}) - {dist:.2f} km")
