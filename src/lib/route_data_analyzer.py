"""
Route data analysis utilities for activities.

This module provides utilities for analyzing activity route data to detect
various characteristics like heart rate monitoring, GPS tracking, and movement
patterns. Used primarily for auto-detection of onsen monitoring activities.
"""

import json
import re
from typing import Optional


def parse_route_data(route_data_json: Optional[str]) -> list[dict]:
    """
    Parse JSON route data string to list of points.

    Args:
        route_data_json: JSON string containing route data points

    Returns:
        List of route data point dictionaries. Empty list if invalid or None.

    Examples:
        >>> parse_route_data('[{"timestamp": "2025-10-30T10:00:00", "hr": 120}]')
        [{'timestamp': '2025-10-30T10:00:00', 'hr': 120}]
    """
    if not route_data_json:
        return []

    try:
        return json.loads(route_data_json)
    except (json.JSONDecodeError, TypeError):
        return []


def has_heart_rate_data(route_data_json: Optional[str]) -> bool:
    """
    Check if route data contains HR measurements.

    Args:
        route_data_json: JSON string containing route data points

    Returns:
        True if at least one point has HR data, False otherwise

    Examples:
        >>> has_heart_rate_data('[{"timestamp": "...", "hr": 120}]')
        True
        >>> has_heart_rate_data('[{"timestamp": "..."}]')
        False
    """
    route_points = parse_route_data(route_data_json)
    return any(point.get("hr") is not None for point in route_points)


def has_gps_data(route_data_json: Optional[str]) -> bool:
    """
    Check if route data contains GPS coordinates.

    Args:
        route_data_json: JSON string containing route data points

    Returns:
        True if at least one point has both lat and lon, False otherwise

    Examples:
        >>> has_gps_data('[{"lat": 33.279, "lon": 131.500}]')
        True
        >>> has_gps_data('[{"hr": 120}]')
        False
    """
    route_points = parse_route_data(route_data_json)
    return any("lat" in point and "lon" in point for point in route_points)


def is_stationary_activity(
    route_data_json: Optional[str],
    speed_threshold: float = 0.5,
    elevation_threshold: float = 5.0,
) -> bool:
    """
    Detect if activity is stationary (HR-only, no movement).

    Stationary activities are identified by:
    - Has HR data
    - No GPS data OR
    - Low average speed (< speed_threshold m/s) AND minimal elevation change (< elevation_threshold m)

    Args:
        route_data_json: JSON string containing route data points
        speed_threshold: Maximum average speed (m/s) for stationary classification
        elevation_threshold: Maximum total elevation change (m) for stationary classification

    Returns:
        True if activity appears stationary, False otherwise

    Examples:
        >>> is_stationary_activity('[{"hr": 120, "speed_mps": 0}]')
        True
        >>> is_stationary_activity('[{"hr": 120, "lat": 33.279, "lon": 131.500, "speed_mps": 3.5}]')
        False
    """
    route_points = parse_route_data(route_data_json)

    if not route_points:
        return False

    # Must have HR data to be considered for stationary classification
    if not has_heart_rate_data(route_data_json):
        return False

    # If no GPS data at all, consider it stationary
    if not has_gps_data(route_data_json):
        return True

    # Check speed: if average speed is low, likely stationary
    speeds = [point.get("speed_mps", 0) for point in route_points]
    avg_speed = sum(speeds) / len(speeds) if speeds else 0

    # Check elevation change: if minimal change, likely stationary
    elevations = [point.get("elevation") for point in route_points if point.get("elevation") is not None]
    if elevations:
        elevation_change = max(elevations) - min(elevations)
    else:
        elevation_change = 0

    # Stationary if both speed is low AND elevation change is minimal
    return avg_speed < speed_threshold and elevation_change < elevation_threshold


def is_onsen_monitoring_by_name(activity_name: str) -> bool:
    """
    Check if activity name indicates onsen monitoring.

    Detects onsen monitoring activities by checking if the name contains:
    - "onsendo" (case-insensitive)
    - AND the number "88" (indicates N/88 format used for tracking)

    Args:
        activity_name: Name of the activity

    Returns:
        True if name matches onsen monitoring pattern, False otherwise

    Examples:
        >>> is_onsen_monitoring_by_name("Onsendo 1/88 - Morning Bath")
        True
        >>> is_onsen_monitoring_by_name("onsendo 42/88")
        True
        >>> is_onsen_monitoring_by_name("Onsen visit")  # Missing "88"
        False
        >>> is_onsen_monitoring_by_name("Morning run")
        False
    """
    if not activity_name:
        return False

    name_lower = activity_name.lower()

    # Must contain "onsendo" (case-insensitive)
    has_onsendo = "onsendo" in name_lower

    # Must contain "88" (indicates N/88 format)
    has_88 = "88" in activity_name

    return has_onsendo and has_88


def calculate_movement_stats(route_data_json: Optional[str]) -> dict:
    """
    Calculate movement statistics from route data.

    Args:
        route_data_json: JSON string containing route data points

    Returns:
        Dictionary with movement statistics:
        - avg_speed: Average speed in m/s (0 if no data)
        - max_speed: Maximum speed in m/s (0 if no data)
        - elevation_change: Total elevation change in meters (0 if no data)
        - has_gps: Whether GPS data is present
        - has_hr: Whether HR data is present
        - point_count: Number of data points

    Examples:
        >>> stats = calculate_movement_stats('[{"hr": 120, "speed_mps": 2.5}]')
        >>> stats['avg_speed']
        2.5
        >>> stats['has_hr']
        True
    """
    route_points = parse_route_data(route_data_json)

    if not route_points:
        return {
            "avg_speed": 0,
            "max_speed": 0,
            "elevation_change": 0,
            "has_gps": False,
            "has_hr": False,
            "point_count": 0,
        }

    # Calculate speed statistics
    speeds = [point.get("speed_mps", 0) for point in route_points]
    avg_speed = sum(speeds) / len(speeds) if speeds else 0
    max_speed = max(speeds) if speeds else 0

    # Calculate elevation change
    elevations = [point.get("elevation") for point in route_points if point.get("elevation") is not None]
    if elevations:
        elevation_change = max(elevations) - min(elevations)
    else:
        elevation_change = 0

    return {
        "avg_speed": avg_speed,
        "max_speed": max_speed,
        "elevation_change": elevation_change,
        "has_gps": has_gps_data(route_data_json),
        "has_hr": has_heart_rate_data(route_data_json),
        "point_count": len(route_points),
    }


def should_classify_as_onsen_monitoring(
    activity_name: str,
    route_data_json: Optional[str],
) -> tuple[bool, str]:
    """
    Determine if activity should be classified as onsen monitoring.

    Combines name-based and route data-based detection to classify activities.
    Returns both the classification decision and the reason for the decision.

    Detection criteria:
    1. Name contains "onsendo" (case-insensitive) AND "88"
    2. Route data shows stationary HR monitoring (no movement, has HR)

    Args:
        activity_name: Name of the activity
        route_data_json: JSON string containing route data points

    Returns:
        Tuple of (should_classify, reason):
        - should_classify: True if should be classified as onsen monitoring
        - reason: Human-readable explanation of the decision

    Examples:
        >>> should_classify_as_onsen_monitoring("Onsendo 1/88", '[{"hr": 120}]')
        (True, 'name pattern + stationary HR')
        >>> should_classify_as_onsen_monitoring("Morning Run", '[{"hr": 140, "speed_mps": 3.5}]')
        (False, 'not onsen monitoring')
    """
    name_match = is_onsen_monitoring_by_name(activity_name)
    stationary = is_stationary_activity(route_data_json)

    if name_match and stationary:
        return (True, "name pattern + stationary HR")
    elif name_match:
        return (True, "name pattern (onsendo + 88)")
    elif stationary:
        # Only stationary is not enough without name match
        # (could be yoga, meditation, etc.)
        return (False, "stationary but no name match")
    else:
        return (False, "not onsen monitoring")
