"""
Unit tests for milestone calculation functionality.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from src.lib.milestone_calculator import (
    calculate_location_milestones,
    analyze_location_distances,
    print_milestone_analysis,
)
from src.lib.distance import DistanceMilestones
from src.db.models import Location, Onsen


class TestCalculateLocationMilestones:
    """Test milestone calculation for locations."""

    def test_calculate_location_milestones_with_onsens(self):
        """Test milestone calculation with valid onsen data."""
        # Create mock location
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        # Create mock onsens with different distances
        onsens = []
        distances = [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]
        
        for i, distance in enumerate(distances):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsen.latitude = 35.6762 + (distance * 0.001)  # Approximate distance
            onsen.longitude = 139.6503
            onsens.append(onsen)
        
        # Mock database session
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.all.return_value = onsens
        
        # Mock distance calculation
        with patch('src.lib.milestone_calculator.calculate_distance_to_onsen') as mock_calc:
            mock_calc.side_effect = lambda loc, onsen: distances[onsen.id - 1]
            
            milestones = calculate_location_milestones(location, mock_session)
        
        # Verify milestones are calculated correctly
        assert isinstance(milestones, DistanceMilestones)
        assert milestones.very_close_max > 0
        assert milestones.close_max > milestones.very_close_max
        assert milestones.medium_max > milestones.close_max
        assert milestones.far_min == milestones.medium_max

    def test_calculate_location_milestones_no_onsens(self):
        """Test milestone calculation with no onsens."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.all.return_value = []
        
        with pytest.raises(ValueError, match="No onsens found in the database"):
            calculate_location_milestones(location, mock_session)

    def test_calculate_location_milestones_no_valid_distances(self):
        """Test milestone calculation with no valid distances."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        # Create onsens with invalid coordinates
        onsens = []
        for i in range(3):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsen.latitude = None  # Invalid coordinates
            onsen.longitude = None
            onsens.append(onsen)
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.all.return_value = onsens
        
        with patch('src.lib.milestone_calculator.calculate_distance_to_onsen') as mock_calc:
            mock_calc.return_value = None  # All distances are None
            
            with pytest.raises(ValueError, match="No valid distances could be calculated"):
                calculate_location_milestones(location, mock_session)

    def test_calculate_location_milestones_quantile_calculation(self):
        """Test that quantiles are calculated correctly."""
        location = Mock(spec=Location)
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        # Create onsens with specific distances for quantile testing
        onsens = []
        distances = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        
        for i, distance in enumerate(distances):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsen.latitude = 35.6762 + (distance * 0.001)
            onsen.longitude = 139.6503
            onsens.append(onsen)
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.all.return_value = onsens
        
        with patch('src.lib.milestone_calculator.calculate_distance_to_onsen') as mock_calc:
            mock_calc.side_effect = lambda loc, onsen: distances[onsen.id - 1]
            
            milestones = calculate_location_milestones(location, mock_session)
        
        # With 10 sorted distances, quantiles should be:
        # 20th percentile (index 1): 2.0
        # 50th percentile (index 4): 5.0  
        # 80th percentile (index 7): 8.0
        assert milestones.very_close_max == 2.0
        assert milestones.close_max == 5.0
        assert milestones.medium_max == 8.0


class TestAnalyzeLocationDistances:
    """Test distance analysis functionality."""

    def test_analyze_location_distances_success(self):
        """Test successful distance analysis."""
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        # Create mock onsens
        onsens = []
        distances = [0.5, 1.0, 2.0, 3.0, 4.0]
        
        for i, distance in enumerate(distances):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsen.name = f"Onsen {i+1}"
            onsen.latitude = 35.6762 + (distance * 0.001)
            onsen.longitude = 139.6503
            onsens.append(onsen)
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.all.return_value = onsens
        
        with patch('src.lib.milestone_calculator.calculate_distance_to_onsen') as mock_calc:
            mock_calc.side_effect = lambda loc, onsen: distances[onsen.id - 1]
            
            analysis = analyze_location_distances(location, mock_session)
        
        # Verify analysis structure
        assert "error" not in analysis
        assert "location" in analysis
        assert "milestones" in analysis
        assert "statistics" in analysis
        assert "onsen_count" in analysis
        assert "sample_distances" in analysis
        
        # Verify location data
        assert analysis["location"]["name"] == "Test Location"
        assert analysis["location"]["latitude"] == 35.6762
        assert analysis["location"]["longitude"] == 139.6503
        
        # Verify milestones
        assert isinstance(analysis["milestones"], DistanceMilestones)
        
        # Verify statistics
        stats = analysis["statistics"]
        assert "mean" in stats
        assert "median" in stats
        assert "min" in stats
        assert "max" in stats
        assert "count" in stats
        assert stats["count"] == 5
        
        # Verify sample distances
        assert len(analysis["sample_distances"]) <= 10
        assert len(analysis["sample_distances"]) == 5  # All distances in this case

    def test_analyze_location_distances_no_onsens(self):
        """Test analysis with no onsens."""
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.all.return_value = []
        
        analysis = analyze_location_distances(location, mock_session)
        
        assert "error" in analysis
        assert analysis["error"] == "No onsens found in the database"

    def test_analyze_location_distances_no_valid_distances(self):
        """Test analysis with no valid distances."""
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        # Create onsens with invalid coordinates
        onsens = []
        for i in range(3):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsen.name = f"Onsen {i+1}"
            onsen.latitude = None
            onsen.longitude = None
            onsens.append(onsen)
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.all.return_value = onsens
        
        with patch('src.lib.milestone_calculator.calculate_distance_to_onsen') as mock_calc:
            mock_calc.return_value = None
            
            analysis = analyze_location_distances(location, mock_session)
        
        assert "error" in analysis
        assert analysis["error"] == "No valid distances could be calculated"

    def test_analyze_location_distances_statistics_calculation(self):
        """Test that statistics are calculated correctly."""
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        # Create onsens with specific distances
        onsens = []
        distances = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        for i, distance in enumerate(distances):
            onsen = Mock(spec=Onsen)
            onsen.id = i + 1
            onsen.name = f"Onsen {i+1}"
            onsen.latitude = 35.6762 + (distance * 0.001)
            onsen.longitude = 139.6503
            onsens.append(onsen)
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.all.return_value = onsens
        
        with patch('src.lib.milestone_calculator.calculate_distance_to_onsen') as mock_calc:
            mock_calc.side_effect = lambda loc, onsen: distances[onsen.id - 1]
            
            analysis = analyze_location_distances(location, mock_session)
        
        stats = analysis["statistics"]
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["count"] == 5
        assert stats["stddev"] is not None  # Should be calculated for >1 distance

    def test_analyze_location_distances_single_distance(self):
        """Test analysis with only one valid distance."""
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        # Create one onsen with valid distance
        onsen = Mock(spec=Onsen)
        onsen.id = 1
        onsen.name = "Single Onsen"
        onsen.latitude = 35.6762 + 0.001
        onsen.longitude = 139.6503
        
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.all.return_value = [onsen]
        
        with patch('src.lib.milestone_calculator.calculate_distance_to_onsen') as mock_calc:
            mock_calc.return_value = 1.0
            
            analysis = analyze_location_distances(location, mock_session)
        
        stats = analysis["statistics"]
        assert stats["mean"] == 1.0
        assert stats["median"] == 1.0
        assert stats["min"] == 1.0
        assert stats["max"] == 1.0
        assert stats["count"] == 1
        assert stats["stddev"] is None  # Cannot calculate stddev for single value


class TestPrintMilestoneAnalysis:
    """Test milestone analysis printing functionality."""

    def test_print_milestone_analysis_success(self, capsys):
        """Test successful analysis printing."""
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        milestones = DistanceMilestones(1.0, 3.0, 5.0, 5.0)
        
        analysis = {
            "location": {
                "name": "Test Location",
                "latitude": 35.6762,
                "longitude": 139.6503,
            },
            "milestones": milestones,
            "statistics": {
                "mean": 3.0,
                "median": 3.0,
                "min": 1.0,
                "max": 5.0,
                "count": 5,
                "stddev": 1.58,
            },
            "onsen_count": 5,
            "sample_distances": [
                (Mock(spec=Onsen, name="Onsen 1", id=1), 1.0),
                (Mock(spec=Onsen, name="Onsen 2", id=2), 2.0),
            ],
        }
        
        print_milestone_analysis(analysis)
        captured = capsys.readouterr()
        
        # Verify output contains expected information
        assert "Test Location" in captured.out
        assert "very_close: <= 1.00 km" in captured.out
        assert "close:      <= 3.00 km" in captured.out
        assert "medium:     <= 5.00 km" in captured.out
        assert "far:        >  5.00 km" in captured.out
        assert "Mean:   3.00 km" in captured.out
        assert "Median: 3.00 km" in captured.out
        assert "Min:    1.00 km" in captured.out
        assert "Max:    5.00 km" in captured.out
        assert "Stddev: 1.58 km" in captured.out

    def test_print_milestone_analysis_with_error(self, capsys):
        """Test analysis printing with error."""
        analysis = {"error": "Test error message"}
        
        print_milestone_analysis(analysis)
        captured = capsys.readouterr()
        
        assert "Error: Test error message" in captured.out

    def test_print_milestone_analysis_no_stddev(self, capsys):
        """Test analysis printing without standard deviation."""
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        milestones = DistanceMilestones(1.0, 1.0, 1.0, 1.0)
        
        analysis = {
            "location": {
                "name": "Test Location",
                "latitude": 35.6762,
                "longitude": 139.6503,
            },
            "milestones": milestones,
            "statistics": {
                "mean": 1.0,
                "median": 1.0,
                "min": 1.0,
                "max": 1.0,
                "count": 1,
                "stddev": None,
            },
            "onsen_count": 1,
            "sample_distances": [],
        }
        
        print_milestone_analysis(analysis)
        captured = capsys.readouterr()
        
        assert "Stddev: N/A (only one onsen)" in captured.out

    def test_print_milestone_analysis_no_sample_distances(self, capsys):
        """Test analysis printing without sample distances."""
        location = Mock(spec=Location)
        location.name = "Test Location"
        location.latitude = 35.6762
        location.longitude = 139.6503
        
        milestones = DistanceMilestones(1.0, 3.0, 5.0, 5.0)
        
        analysis = {
            "location": {
                "name": "Test Location",
                "latitude": 35.6762,
                "longitude": 139.6503,
            },
            "milestones": milestones,
            "statistics": {
                "mean": 3.0,
                "median": 3.0,
                "min": 1.0,
                "max": 5.0,
                "count": 5,
                "stddev": 1.58,
            },
            "onsen_count": 5,
            "sample_distances": [],
        }
        
        print_milestone_analysis(analysis)
        captured = capsys.readouterr()
        
        # Should not contain sample distances section
        assert "Sample Distances" not in captured.out
