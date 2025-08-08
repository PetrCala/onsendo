"""
Integration tests for distance calculation, milestone calculation, and recommendation functionality.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from src.lib.distance import (
    haversine_distance,
    calculate_distance_to_onsen,
    filter_onsens_by_distance,
    DistanceMilestones,
    update_distance_categories,
    reset_distance_categories,
)
from src.lib.milestone_calculator import (
    calculate_location_milestones,
    analyze_location_distances,
)
from src.lib.recommendation import OnsenRecommendationEngine
from src.db.models import Location, Onsen


class TestDistanceCalculationIntegration:
    """Integration tests for distance calculation."""

    def test_real_distance_calculation(self, db_session: Session):
        """Test distance calculation with real coordinates."""
        # Create a test location
        location = Location(
            name="Test Location",
            latitude=35.6762,  # Tokyo
            longitude=139.6503,
            description="Test location for distance calculation"
        )
        db_session.add(location)
        db_session.commit()
        
        # Create test onsens at different distances
        onsens = []
        test_coordinates = [
            (35.6762, 139.6503),  # Same location (0 km)
            (35.6762, 139.6603),  # ~1 km away
            (35.6862, 139.6503),  # ~1 km away
            (35.6762, 139.7503),  # ~10 km away
        ]
        
        for i, (lat, lon) in enumerate(test_coordinates):
            onsen = Onsen(
                ban_number=f"TEST{i+1}",
                name=f"Test Onsen {i+1}",
                address=f"Test Address {i+1}",
                latitude=lat,
                longitude=lon
            )
            onsens.append(onsen)
            db_session.add(onsen)
        
        db_session.commit()
        
        # Test distance calculations
        distances = []
        for onsen in onsens:
            distance = calculate_distance_to_onsen(location, onsen)
            distances.append(distance)
            assert distance is not None
            assert distance >= 0
        
        # Verify expected distances (with some tolerance)
        assert distances[0] == 0.0  # Same location
        assert 0.8 <= distances[1] <= 1.2  # ~1 km
        assert 0.8 <= distances[2] <= 1.2  # ~1 km
        assert 8.0 <= distances[3] <= 12.0  # ~10 km

    def test_distance_filtering_integration(self, db_session: Session):
        """Test distance filtering with real data."""
        # Create a test location
        location = Location(
            name="Test Location",
            latitude=35.6762,
            longitude=139.6503,
            description="Test location for filtering"
        )
        db_session.add(location)
        db_session.commit()
        
        # Create test onsens at different distances
        onsens = []
        test_distances = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]
        
        for i, distance in enumerate(test_distances):
            # Approximate coordinates for the distance
            lat_offset = distance * 0.001  # Rough approximation
            onsen = Onsen(
                ban_number=f"TEST{i+1}",
                name=f"Test Onsen {i+1}",
                address=f"Test Address {i+1}",
                latitude=35.6762 + lat_offset,
                longitude=139.6503
            )
            onsens.append(onsen)
            db_session.add(onsen)
        
        db_session.commit()
        
        # Test filtering by different categories
        very_close_results = filter_onsens_by_distance(onsens, location, "very_close")
        close_results = filter_onsens_by_distance(onsens, location, "close")
        medium_results = filter_onsens_by_distance(onsens, location, "medium")
        far_results = filter_onsens_by_distance(onsens, location, "far")
        
        # Verify results are sorted by distance
        for results in [very_close_results, close_results, medium_results, far_results]:
            if len(results) >= 2:
                for i in range(len(results) - 1):
                    assert results[i][1] <= results[i + 1][1]


class TestMilestoneCalculationIntegration:
    """Integration tests for milestone calculation."""

    def test_milestone_calculation_with_real_data(self, db_session: Session):
        """Test milestone calculation with real onsen data."""
        # Create a test location
        location = Location(
            name="Test Location",
            latitude=35.6762,
            longitude=139.6503,
            description="Test location for milestones"
        )
        db_session.add(location)
        db_session.commit()
        
        # Create test onsens with specific distances
        onsens = []
        test_distances = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        
        for i, distance in enumerate(test_distances):
            lat_offset = distance * 0.001
            onsen = Onsen(
                ban_number=f"TEST{i+1}",
                name=f"Test Onsen {i+1}",
                address=f"Test Address {i+1}",
                latitude=35.6762 + lat_offset,
                longitude=139.6503
            )
            onsens.append(onsen)
            db_session.add(onsen)
        
        db_session.commit()
        
        # Calculate milestones
        milestones = calculate_location_milestones(location, db_session)
        
        # Verify milestone structure
        assert isinstance(milestones, DistanceMilestones)
        assert milestones.very_close_max > 0
        assert milestones.close_max > milestones.very_close_max
        assert milestones.medium_max > milestones.close_max
        assert milestones.far_min == milestones.medium_max
        
        # With 10 sorted distances, quantiles should be:
        # 20th percentile (index 1): 2.0
        # 50th percentile (index 4): 5.0
        # 80th percentile (index 7): 8.0
        assert milestones.very_close_max == 2.0
        assert milestones.close_max == 5.0
        assert milestones.medium_max == 8.0

    def test_analysis_integration(self, db_session: Session):
        """Test complete analysis with real data."""
        # Create a test location
        location = Location(
            name="Test Location",
            latitude=35.6762,
            longitude=139.6503,
            description="Test location for analysis"
        )
        db_session.add(location)
        db_session.commit()
        
        # Create test onsens
        onsens = []
        test_distances = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for i, distance in enumerate(test_distances):
            lat_offset = distance * 0.001
            onsen = Onsen(
                ban_number=f"TEST{i+1}",
                name=f"Test Onsen {i+1}",
                address=f"Test Address {i+1}",
                latitude=35.6762 + lat_offset,
                longitude=139.6503
            )
            onsens.append(onsen)
            db_session.add(onsen)
        
        db_session.commit()
        
        # Perform analysis
        analysis = analyze_location_distances(location, db_session)
        
        # Verify analysis structure
        assert "error" not in analysis
        assert "location" in analysis
        assert "milestones" in analysis
        assert "statistics" in analysis
        assert "onsen_count" in analysis
        assert "sample_distances" in analysis
        
        # Verify statistics
        stats = analysis["statistics"]
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["count"] == 5
        assert stats["stddev"] is not None

    def test_distance_category_updates(self, db_session: Session):
        """Test that distance categories are updated correctly."""
        # Create a test location
        location = Location(
            name="Test Location",
            latitude=35.6762,
            longitude=139.6503,
            description="Test location for category updates"
        )
        db_session.add(location)
        db_session.commit()
        
        # Create test onsens
        onsens = []
        test_distances = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for i, distance in enumerate(test_distances):
            lat_offset = distance * 0.001
            onsen = Onsen(
                ban_number=f"TEST{i+1}",
                name=f"Test Onsen {i+1}",
                address=f"Test Address {i+1}",
                latitude=35.6762 + lat_offset,
                longitude=139.6503
            )
            onsens.append(onsen)
            db_session.add(onsen)
        
        db_session.commit()
        
        # Calculate milestones and update categories
        milestones = calculate_location_milestones(location, db_session)
        update_distance_categories(milestones)
        
        # Test filtering with updated categories
        from src.lib.distance import DISTANCE_CATEGORIES
        
        # Verify categories were updated
        assert DISTANCE_CATEGORIES["very_close"].max_distance_km == milestones.very_close_max
        assert DISTANCE_CATEGORIES["close"].max_distance_km == milestones.close_max
        assert DISTANCE_CATEGORIES["medium"].max_distance_km == milestones.medium_max
        
        # Test filtering with new categories
        very_close_results = filter_onsens_by_distance(onsens, location, "very_close")
        close_results = filter_onsens_by_distance(onsens, location, "close")
        medium_results = filter_onsens_by_distance(onsens, location, "medium")
        far_results = filter_onsens_by_distance(onsens, location, "far")
        
        # Verify exclusive filtering works
        assert len(very_close_results) == 1  # Only distance 1.0
        assert len(close_results) == 1       # Only distance 2.0
        assert len(medium_results) == 1      # Only distance 3.0
        assert len(far_results) == 2         # Distances 4.0 and 5.0
        
        # Reset categories
        reset_distance_categories()


class TestRecommendationEngineIntegration:
    """Integration tests for recommendation engine."""

    def test_recommendation_engine_with_real_data(self, db_session: Session):
        """Test recommendation engine with real data."""
        # Create a test location
        location = Location(
            name="Test Location",
            latitude=35.6762,
            longitude=139.6503,
            description="Test location for recommendations"
        )
        db_session.add(location)
        db_session.commit()
        
        # Create test onsens
        onsens = []
        test_distances = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
        
        for i, distance in enumerate(test_distances):
            lat_offset = distance * 0.001
            onsen = Onsen(
                ban_number=f"TEST{i+1}",
                name=f"Test Onsen {i+1}",
                address=f"Test Address {i+1}",
                latitude=35.6762 + lat_offset,
                longitude=139.6503,
                usage_time="6:00～22:00",  # Always open
                admission_fee="500円"
            )
            onsens.append(onsen)
            db_session.add(onsen)
        
        db_session.commit()
        
        # Create recommendation engine
        engine = OnsenRecommendationEngine(db_session, location)
        
        # Test recommendations for different categories
        very_close_recs = engine.recommend_onsens(
            location=location,
            distance_category="very_close",
            exclude_closed=False,
            exclude_visited=False
        )
        
        close_recs = engine.recommend_onsens(
            location=location,
            distance_category="close",
            exclude_closed=False,
            exclude_visited=False
        )
        
        medium_recs = engine.recommend_onsens(
            location=location,
            distance_category="medium",
            exclude_closed=False,
            exclude_visited=False
        )
        
        far_recs = engine.recommend_onsens(
            location=location,
            distance_category="far",
            exclude_closed=False,
            exclude_visited=False
        )
        
        # Verify recommendations
        assert len(very_close_recs) == 1  # Distance 0.5
        assert len(close_recs) == 1       # Distance 1.0
        assert len(medium_recs) == 1      # Distance 2.0
        assert len(far_recs) == 3         # Distances 3.0, 4.0, 5.0
        
        # Verify metadata
        for recs in [very_close_recs, close_recs, medium_recs, far_recs]:
            for onsen, distance, metadata in recs:
                assert "distance_category" in metadata
                assert "is_available" in metadata
                assert "has_been_visited" in metadata
                assert metadata["is_available"] == True  # All onsens are always open

    def test_recommendation_engine_with_limits(self, db_session: Session):
        """Test recommendation engine with limits."""
        # Create a test location
        location = Location(
            name="Test Location",
            latitude=35.6762,
            longitude=139.6503,
            description="Test location for limited recommendations"
        )
        db_session.add(location)
        db_session.commit()
        
        # Create test onsens
        onsens = []
        test_distances = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for i, distance in enumerate(test_distances):
            lat_offset = distance * 0.001
            onsen = Onsen(
                ban_number=f"TEST{i+1}",
                name=f"Test Onsen {i+1}",
                address=f"Test Address {i+1}",
                latitude=35.6762 + lat_offset,
                longitude=139.6503,
                usage_time="6:00～22:00"
            )
            onsens.append(onsen)
            db_session.add(onsen)
        
        db_session.commit()
        
        # Create recommendation engine
        engine = OnsenRecommendationEngine(db_session, location)
        
        # Test with limit
        recommendations = engine.recommend_onsens(
            location=location,
            distance_category="far",
            exclude_closed=False,
            exclude_visited=False,
            limit=2
        )
        
        assert len(recommendations) == 2

    def test_recommendation_engine_location_management(self, db_session: Session):
        """Test recommendation engine location management."""
        # Create test locations
        location1 = Location(
            name="Location 1",
            latitude=35.6762,
            longitude=139.6503,
            description="First test location"
        )
        location2 = Location(
            name="Location 2",
            latitude=35.6862,  # Different location
            longitude=139.6603,
            description="Second test location"
        )
        db_session.add(location1)
        db_session.add(location2)
        db_session.commit()
        
        # Create test onsens
        onsen = Onsen(
            ban_number="TEST1",
            name="Test Onsen",
            address="Test Address",
            latitude=35.6762 + 0.001,  # Close to location 1
            longitude=139.6503,
            usage_time="6:00～22:00"
        )
        db_session.add(onsen)
        db_session.commit()
        
        # Create engine with first location
        engine = OnsenRecommendationEngine(db_session, location1)
        
        # Get recommendations
        recs1 = engine.recommend_onsens(
            location=location1,
            distance_category="very_close",
            exclude_closed=False,
            exclude_visited=False
        )
        
        # Update to second location
        engine.update_location(location2)
        
        # Get recommendations for second location
        recs2 = engine.recommend_onsens(
            location=location2,
            distance_category="very_close",
            exclude_closed=False,
            exclude_visited=False
        )
        
        # The onsen should be close to location 1 but far from location 2
        assert len(recs1) > 0
        assert len(recs2) == 0  # Should be too far for very_close category
