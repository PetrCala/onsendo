"""
Onsen recommendation engine.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db.models import Onsen, Location, OnsenVisit
from src.lib.parsers.usage_time import parse_usage_time
from src.lib.parsers.closed_days import parse_closed_days
from src.lib.distance import filter_onsens_by_distance, calculate_distance_to_onsen


class OnsenRecommendationEngine:
    """Engine for recommending onsens based on various criteria."""

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_available_onsens(self, target_time: datetime) -> List[Onsen]:
        """
        Get onsens that are open at the specified time.

        Args:
            target_time: The time to check availability for

        Returns:
            List of available onsens
        """
        # Get all onsens
        onsens = self.db_session.query(Onsen).all()
        available_onsens = []

        for onsen in onsens:
            if self._is_onsen_available(onsen, target_time):
                available_onsens.append(onsen)

        return available_onsens

    def _is_onsen_available(self, onsen: Onsen, target_time: datetime) -> bool:
        """
        Check if an onsen is available at the specified time.

        Args:
            onsen: Onsen to check
            target_time: Time to check availability for

        Returns:
            True if the onsen is available, False otherwise
        """
        # Check usage time
        if onsen.usage_time:
            usage_parsed = parse_usage_time(onsen.usage_time)
            if not usage_parsed.is_open(target_time, assume_unknown_closed=True):
                return False

        # Check closed days
        if onsen.closed_days:
            closed_parsed = parse_closed_days(onsen.closed_days)
            if closed_parsed.is_closed_on(target_time):
                return False

        return True

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
            onsens = self.get_available_onsens(target_time)

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
                    self._is_onsen_available(onsen, target_time)
                    if not exclude_closed
                    else True
                ),
                "has_been_visited": self._has_been_visited(onsen),
            }
            recommendations.append((onsen, distance, metadata))

            if limit and len(recommendations) >= limit:
                break

        return recommendations

    def _get_distance_category_name(self, distance_km: float) -> str:
        """Get distance category name for a given distance."""
        if distance_km <= 5.0:
            return "very_close"
        elif distance_km <= 15.0:
            return "close"
        elif distance_km <= 50.0:
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
