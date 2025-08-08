"""
Onsen recommendation engine.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db.models import Onsen, Location, OnsenVisit
from src.lib.parsers.usage_time import parse_usage_time
from src.lib.parsers.closed_days import parse_closed_days
from src.lib.distance import (
    filter_onsens_by_distance,
    update_distance_categories,
    DistanceMilestones,
)
from src.lib.milestone_calculator import calculate_location_milestones
from src.lib.utils import generate_google_maps_link


class OnsenRecommendationEngine:
    """Engine for recommending onsens based on various criteria."""

    def __init__(self, db_session: Session, location: Optional[Location] = None):
        self.db_session = db_session
        self.location = location
        self._distance_milestones: Optional[DistanceMilestones] = None

        # Calculate distance milestones if location is provided
        if location:
            self._calculate_and_update_milestones(location)

    def get_available_onsens(
        self, target_time: datetime, min_hours_after: Optional[int] = None
    ) -> List[Onsen]:
        """
        Get onsens that are open at the specified time.

        Args:
            target_time: The time to check availability for
            min_hours_after: Minimum hours the onsen should be open after target_time (None to disable)

        Returns:
            List of available onsens
        """
        # Get all onsens
        onsens = self.db_session.query(Onsen).all()
        available_onsens = []

        for onsen in onsens:
            if self._is_onsen_available(onsen, target_time, min_hours_after):
                available_onsens.append(onsen)

        return available_onsens

    def _is_onsen_available(
        self, onsen: Onsen, target_time: datetime, min_hours_after: Optional[int] = None
    ) -> bool:
        """
        Check if an onsen is available at the specified time.

        Args:
            onsen: Onsen to check
            target_time: Time to check availability for
            min_hours_after: Minimum hours the onsen should be open after target_time (None to disable)

        Returns:
            True if the onsen is available, False otherwise
        """
        # Check usage time
        if onsen.usage_time:
            usage_parsed = parse_usage_time(onsen.usage_time)
            if not usage_parsed.is_open(target_time, assume_unknown_closed=True):
                return False

            # Check if onsen is open for minimum hours after target time
            if min_hours_after is not None:
                if not self._is_onsen_open_for_minimum_hours(
                    onsen, target_time, min_hours_after
                ):
                    return False

        # Check closed days
        if onsen.closed_days:
            closed_parsed = parse_closed_days(onsen.closed_days)
            if closed_parsed.is_closed_on(target_time):
                return False

        return True

    def _is_onsen_open_for_minimum_hours(
        self, onsen: Onsen, target_time: datetime, min_hours: int
    ) -> bool:
        """
        Check if an onsen is open for at least the specified number of hours after the target time.

        Args:
            onsen: Onsen to check
            target_time: The time to check from
            min_hours: Minimum hours the onsen should be open

        Returns:
            True if the onsen is open for at least min_hours after target_time
        """
        if not onsen.usage_time:
            return False

        usage_parsed = parse_usage_time(onsen.usage_time)

        # Check each time window
        for window in usage_parsed.windows:
            if not window.applies_on(target_time):
                continue

            # If window has no end time, assume it's open long enough
            if window.end_time is None:
                return True

            # Calculate end time of the window
            window_end = datetime.combine(target_time.date(), window.end_time)
            if window.end_next_day:
                window_end = window_end + timedelta(days=1)

            # Calculate target end time
            target_end = target_time + timedelta(hours=min_hours)

            # Check if window extends far enough
            if window_end >= target_end:
                return True

        return False

    def get_unvisited_onsens(self, onsens: List[Onsen]) -> List[Onsen]:
        """
        Filter out onsens that have been visited.

        Args:
            onsens: List of onsens to filter

        Returns:
            List of unvisited onsens
        """
        # Get all onsen IDs that have been visited
        visited_onsen_ids = set(
            self.db_session.query(OnsenVisit.onsen_id).distinct().all()
        )
        visited_onsen_ids = {id_tuple[0] for id_tuple in visited_onsen_ids}

        # Filter out visited onsens
        unvisited_onsens = [
            onsen for onsen in onsens if onsen.id not in visited_onsen_ids
        ]

        return unvisited_onsens

    def recommend_onsens(
        self,
        location: Location,
        target_time: Optional[datetime] = None,
        distance_category: str = "medium",
        exclude_closed: bool = True,
        exclude_visited: bool = False,
        min_hours_after: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Tuple[Onsen, float, dict]]:
        """
        Get onsen recommendations based on specified criteria.

        Args:
            location: User's location
            target_time: Time to check availability for (defaults to now)
            distance_category: Distance category (very_close, close, medium, far)
            exclude_closed: Whether to exclude closed onsens
            exclude_visited: Whether to exclude visited onsens
            min_hours_after: Minimum hours the onsen should be open after target_time (None to disable)
            limit: Maximum number of recommendations to return

        Returns:
            List of tuples (onsen, distance_km, metadata)
        """
        if target_time is None:
            target_time = datetime.now()

        # Start with all onsens
        onsens = self.db_session.query(Onsen).all()

        # Filter by availability if requested
        if exclude_closed:
            onsens = self.get_available_onsens(target_time, min_hours_after)

        # Filter by visit history if requested
        if exclude_visited:
            onsens = self.get_unvisited_onsens(onsens)

        # Filter by distance
        distance_filtered = filter_onsens_by_distance(
            onsens, location, distance_category
        )

        # Add metadata and limit results
        recommendations = []
        for onsen, distance in distance_filtered:
            metadata = {
                "distance_category": self._get_distance_category_name(distance),
                "is_available": (
                    self._is_onsen_available(onsen, target_time, min_hours_after)
                    if not exclude_closed
                    else True
                ),
                "has_been_visited": self._has_been_visited(onsen),
                "google_maps_link": self._generate_google_maps_link(onsen),
            }
            recommendations.append((onsen, distance, metadata))

            if limit and len(recommendations) >= limit:
                break

        return recommendations

    def _calculate_and_update_milestones(self, location: Location) -> None:
        """Calculate and update distance milestones for the given location."""
        self._distance_milestones = calculate_location_milestones(
            location, self.db_session
        )
        update_distance_categories(self._distance_milestones)

    def update_location(self, location: Location) -> None:
        """Update the location and recalculate distance milestones."""
        self.location = location
        self._calculate_and_update_milestones(location)

    def get_distance_milestones(self) -> Optional[DistanceMilestones]:
        """Get the current distance milestones."""
        return self._distance_milestones

    def print_distance_milestones(self) -> None:
        """Print the current distance milestones."""
        if not self._distance_milestones:
            print("No distance milestones calculated. Set a location first.")
            return

        print(f"Distance Milestones for {self.location.name}:")
        print(f"  Very Close: <= {self._distance_milestones.very_close_max:.2f} km")
        print(f"  Close:      <= {self._distance_milestones.close_max:.2f} km")
        print(f"  Medium:     <= {self._distance_milestones.medium_max:.2f} km")
        print(f"  Far:        >  {self._distance_milestones.medium_max:.2f} km")

    def _get_distance_category_name(self, distance_km: float) -> str:
        """Get distance category name for a given distance."""
        if not self._distance_milestones:
            # Fallback to default categories
            if distance_km <= 5.0:
                return "very_close"
            elif distance_km <= 15.0:
                return "close"
            elif distance_km <= 50.0:
                return "medium"
            else:
                return "far"

        # Use dynamic milestones
        if distance_km <= self._distance_milestones.very_close_max:
            return "very_close"
        elif distance_km <= self._distance_milestones.close_max:
            return "close"
        elif distance_km <= self._distance_milestones.medium_max:
            return "medium"
        else:
            return "far"

    def _has_been_visited(self, onsen: Onsen) -> bool:
        """Check if an onsen has been visited."""
        return (
            self.db_session.query(OnsenVisit)
            .filter(OnsenVisit.onsen_id == onsen.id)
            .first()
            is not None
        )

    def _generate_google_maps_link(self, onsen: Onsen) -> str:
        """Generate a Google Maps link for an onsen."""
        return generate_google_maps_link(onsen)

    def get_location_by_name_or_id(self, identifier: str) -> Optional[Location]:
        """
        Get a location by name or ID.

        Args:
            identifier: Location name or ID string

        Returns:
            Location object or None if not found
        """
        # Try to parse as ID first
        try:
            location_id = int(identifier)
            return (
                self.db_session.query(Location)
                .filter(Location.id == location_id)
                .first()
            )
        except ValueError:
            pass

        # Try to find by name
        return (
            self.db_session.query(Location).filter(Location.name == identifier).first()
        )

    def list_locations(self) -> List[Location]:
        """Get all locations."""
        return self.db_session.query(Location).order_by(Location.name).all()
