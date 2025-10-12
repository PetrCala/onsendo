"""Onsen recommendation engine."""

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session, load_only

from src.db.models import Onsen, Location, OnsenVisit
from src.lib.parsers.usage_time import parse_usage_time
from src.lib.parsers.closed_days import parse_closed_days
from src.lib.parsers.stay_restriction import parse_stay_restriction
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
        self._usage_time_cache: Dict[int, Tuple[Optional[str], Any]] = {}
        self._closed_days_cache: Dict[int, Tuple[Optional[str], Any]] = {}
        self._stay_restriction_cache: Dict[int, Tuple[Optional[str], Any]] = {}
        self._visited_onsen_ids: Optional[Set[int]] = None
        self._visit_cache_supported: bool = True

        # Calculate distance milestones if location is provided
        if location:
            self._calculate_and_update_milestones(location)

    def get_available_onsens(
        self,
        target_time: datetime,
        min_hours_after: Optional[int] = None,
        onsens: Optional[List[Onsen]] = None,
    ) -> List[Onsen]:
        """
        Get onsens that are open at the specified time.

        Args:
            target_time: The time to check availability for
            min_hours_after: Minimum hours the onsen should be open after target_time (None to disable)

        Returns:
            List of available onsens
        """
        # Get all onsens if not provided
        onsens = onsens if onsens is not None else self.db_session.query(Onsen).all()
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
        usage_parsed = self._get_usage_time_parsed(onsen)
        if usage_parsed is not None:
            if not usage_parsed.is_open(target_time, assume_unknown_closed=True):
                return False

            # Check if onsen is open for minimum hours after target time
            if min_hours_after is not None:
                if not self._is_onsen_open_for_minimum_hours(
                    onsen, target_time, min_hours_after
                ):
                    return False

        # Check closed days
        closed_parsed = self._get_closed_days_parsed(onsen)
        if closed_parsed is not None and closed_parsed.is_closed_on(target_time):
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
        usage_parsed = self._get_usage_time_parsed(onsen)
        if usage_parsed is None:
            return False

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
        visited_onsen_ids = self._get_visited_onsen_ids()

        # Filter out visited onsens
        unvisited_onsens = [
            onsen for onsen in onsens if onsen.id not in visited_onsen_ids
        ]

        return unvisited_onsens

    def get_non_stay_restricted_onsens(self, onsens: List[Onsen]) -> List[Onsen]:
        """
        Filter out onsens that are restricted to facility guests only.

        Args:
            onsens: List of onsens to filter

        Returns:
            List of non-stay-restricted onsens
        """
        non_stay_restricted = []

        for onsen in onsens:
            stay_restriction = self._get_stay_restriction(onsen)
            if stay_restriction is None or not stay_restriction.is_stay_restricted:
                non_stay_restricted.append(onsen)

        return non_stay_restricted

    def recommend_onsens(
        self,
        location: Location,
        target_time: Optional[datetime] = None,
        distance_category: str = "medium",
        exclude_closed: bool = True,
        exclude_visited: bool = False,
        min_hours_after: Optional[int] = None,
        limit: Optional[int] = None,
        stay_restriction_filter: Optional[str] = None,
    ) -> List[Tuple[Onsen, float, dict]]:
        """
        Get onsen recommendations based on specified criteria.

        Args:
            location: User's location
            target_time: Time to check availability for (defaults to now)
            distance_category: Distance category (very_close, close, medium, far, any)
            exclude_closed: Whether to exclude closed onsens
            exclude_visited: Whether to exclude visited onsens
            min_hours_after: Minimum hours the onsen should be open after target_time (None to disable)
            limit: Maximum number of recommendations to return
            stay_restriction_filter: Filter for stay restrictions ('non_stay_restricted', 'all', or None)

        Returns:
            List of tuples (onsen, distance_km, metadata)
        """
        if target_time is None:
            target_time = datetime.now()

        # Refresh visit cache for each recommendation request to keep data accurate
        self._visited_onsen_ids = None

        # Start with onsens scoped to the requested distance bucket to avoid
        # scanning the entire catalogue on every request.
        onsens = self._get_candidate_onsens(location, distance_category)

        # Filter by availability if requested
        if exclude_closed:
            onsens = self.get_available_onsens(
                target_time, min_hours_after, onsens=onsens
            )

        # Filter by visit history if requested
        if exclude_visited:
            onsens = self.get_unvisited_onsens(onsens)

        # Filter by stay restriction if requested
        if stay_restriction_filter == "non_stay_restricted":
            onsens = self.get_non_stay_restricted_onsens(onsens)

        # Filter by distance
        distance_filtered = filter_onsens_by_distance(
            onsens,
            location,
            distance_category,
            limit=limit if limit and limit > 0 else None,
        )

        # Add metadata and limit results
        recommendations = []
        for onsen, distance in distance_filtered:
            # Parse stay restriction for metadata
            stay_restriction = self._get_stay_restriction(onsen)

            metadata = {
                "distance_category": self._get_distance_category_name(distance),
                "is_available": (
                    self._is_onsen_available(onsen, target_time, min_hours_after)
                    if not exclude_closed
                    else True
                ),
                "has_been_visited": self._has_been_visited(onsen),
                "google_maps_link": self._generate_google_maps_link(onsen),
                "stay_restricted": (
                    stay_restriction.is_stay_restricted if stay_restriction else False
                ),
                "stay_restriction_notes": (
                    stay_restriction.notes if stay_restriction else None
                ),
            }
            recommendations.append((onsen, distance, metadata))

            if limit and len(recommendations) >= limit:
                break

        return recommendations

    def _get_candidate_onsens(
        self, location: Location, distance_category: str
    ) -> List[Onsen]:
        """Return onsens roughly matching the requested distance bucket."""

        query = self.db_session.query(Onsen).options(
            load_only(
                Onsen.id,
                Onsen.ban_number,
                Onsen.name,
                Onsen.address,
                Onsen.latitude,
                Onsen.longitude,
                Onsen.usage_time,
                Onsen.closed_days,
                Onsen.admission_fee,
                Onsen.remarks,
            )
        )

        radius_km = self._get_distance_radius_for_category(distance_category)

        if (
            radius_km is not None
            and location.latitude is not None
            and location.longitude is not None
        ):
            # Latitude degrees are ~111km apart. Longitude shrinks by cos(latitude).
            lat_delta = radius_km / 111.0
            cos_lat = math.cos(math.radians(location.latitude))
            if abs(cos_lat) < 1e-6:
                lon_delta = 180.0
            else:
                lon_delta = radius_km / (111.320 * cos_lat)

            lat_min = location.latitude - lat_delta
            lat_max = location.latitude + lat_delta
            lon_min = location.longitude - lon_delta
            lon_max = location.longitude + lon_delta

            query = query.filter(Onsen.latitude.isnot(None)).filter(
                Onsen.longitude.isnot(None)
            )
            query = query.filter(Onsen.latitude.between(lat_min, lat_max)).filter(
                Onsen.longitude.between(lon_min, lon_max)
            )

        return query.all()

    def _get_distance_radius_for_category(self, distance_category: str) -> Optional[float]:
        """Return an approximate radius to use for the provided distance bucket."""

        milestones = self._distance_milestones

        if distance_category == "very_close":
            return (milestones.very_close_max if milestones else 5.0)
        if distance_category == "close":
            return (milestones.close_max if milestones else 15.0)
        if distance_category == "medium":
            return (milestones.medium_max if milestones else 50.0)

        # For "far" and "any" we intentionally avoid clamping results so that callers can
        # still explore the full catalogue.
        return None

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
        visited_ids = self._get_visited_onsen_ids()
        if not self._visit_cache_supported:
            return (
                self.db_session.query(OnsenVisit)
                .filter(OnsenVisit.onsen_id == onsen.id)
                .first()
                is not None
            )
        return onsen.id in visited_ids

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

    def _get_usage_time_parsed(self, onsen: Onsen):
        if not onsen.usage_time:
            return None

        cached = self._usage_time_cache.get(onsen.id)
        if cached and cached[0] == onsen.usage_time:
            return cached[1]

        parsed = parse_usage_time(onsen.usage_time)
        self._usage_time_cache[onsen.id] = (onsen.usage_time, parsed)
        return parsed

    def _get_closed_days_parsed(self, onsen: Onsen):
        if not onsen.closed_days:
            return None

        cached = self._closed_days_cache.get(onsen.id)
        if cached and cached[0] == onsen.closed_days:
            return cached[1]

        parsed = parse_closed_days(onsen.closed_days)
        self._closed_days_cache[onsen.id] = (onsen.closed_days, parsed)
        return parsed

    def _get_stay_restriction(self, onsen: Onsen):
        remarks = onsen.remarks or ""
        cached = self._stay_restriction_cache.get(onsen.id)
        if cached and cached[0] == remarks:
            return cached[1]

        parsed = parse_stay_restriction(remarks)
        self._stay_restriction_cache[onsen.id] = (remarks, parsed)
        return parsed

    def _get_visited_onsen_ids(self) -> Set[int]:
        if self._visited_onsen_ids is None:
            try:
                visited_rows = (
                    self.db_session.query(OnsenVisit.onsen_id).distinct().all()
                )
                ids: Set[int] = set()
                for row in visited_rows:
                    if isinstance(row, (tuple, list)):
                        ids.add(row[0])
                    else:
                        onsen_id = getattr(row, "onsen_id", None)
                        if onsen_id is not None:
                            ids.add(onsen_id)
                self._visited_onsen_ids = ids
            except TypeError:
                # Some mocked sessions return non-iterable placeholders; disable caching
                self._visit_cache_supported = False
                self._visited_onsen_ids = set()
            except Exception:
                self._visit_cache_supported = False
                self._visited_onsen_ids = set()
            else:
                self._visit_cache_supported = True
        return self._visited_onsen_ids
