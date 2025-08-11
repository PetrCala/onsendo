"""
Unit tests for heart rate data management system.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta

from src.lib.heart_rate_manager import (
    HeartRatePoint,
    HeartRateSession,
    HeartRateDataValidator,
    HeartRateDataImporter
)


class TestHeartRatePoint:
    """Test HeartRatePoint dataclass."""
    
    def test_heart_rate_point_creation(self):
        """Test creating a heart rate point."""
        point = HeartRatePoint(
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            heart_rate=72.0,
            confidence=0.95
        )
        
        assert point.timestamp == datetime(2024, 1, 15, 10, 0, 0)
        assert point.heart_rate == 72.0
        assert point.confidence == 0.95
    
    def test_heart_rate_point_defaults(self):
        """Test heart rate point with default confidence."""
        point = HeartRatePoint(
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            heart_rate=72.0
        )
        
        assert point.confidence is None


class TestHeartRateSession:
    """Test HeartRateSession dataclass."""
    
    def test_session_properties(self):
        """Test session property calculations."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 30, 0)
        
        data_points = [
            HeartRatePoint(start_time + timedelta(minutes=i), 70 + i)
            for i in range(31)  # 31 points over 30 minutes
        ]
        
        session = HeartRateSession(
            start_time=start_time,
            end_time=end_time,
            data_points=data_points,
            format='csv',
            source_file='test.csv'
        )
        
        assert session.duration_minutes == 30
        assert session.data_points_count == 31
        assert session.average_heart_rate == 85.0  # (70 + 100) / 2
        assert session.min_heart_rate == 70.0
        assert session.max_heart_rate == 100.0
    
    def test_empty_session(self):
        """Test session with no data points."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 1, 0)
        
        session = HeartRateSession(
            start_time=start_time,
            end_time=end_time,
            data_points=[],
            format='csv',
            source_file='test.csv'
        )
        
        assert session.duration_minutes == 1
        assert session.data_points_count == 0
        assert session.average_heart_rate == 0.0
        assert session.min_heart_rate == 0.0
        assert session.max_heart_rate == 0.0


class TestHeartRateDataValidator:
    """Test HeartRateDataValidator class."""
    
    def test_valid_session(self):
        """Test validation of a valid session."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 10, 0)
        
        data_points = [
            HeartRatePoint(start_time + timedelta(minutes=i), 70 + i)
            for i in range(11)  # 11 points over 10 minutes
        ]
        
        session = HeartRateSession(
            start_time=start_time,
            end_time=end_time,
            data_points=data_points,
            format='csv',
            source_file='test.csv'
        )
        
        is_valid, errors = HeartRateDataValidator.validate_session(session)
        assert is_valid
        assert len(errors) == 0
    
    def test_session_too_short(self):
        """Test validation of session that's too short."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 0, 30)  # 30 seconds
        
        data_points = [
            HeartRatePoint(start_time + timedelta(seconds=i*10), 70 + i)
            for i in range(4)  # 4 points over 30 seconds
        ]
        
        session = HeartRateSession(
            start_time=start_time,
            end_time=end_time,
            data_points=data_points,
            format='csv',
            source_file='test.csv'
        )
        
        is_valid, errors = HeartRateDataValidator.validate_session(session)
        assert not is_valid
        assert any("too short" in error for error in errors)
    
    def test_session_too_few_points(self):
        """Test validation of session with too few data points."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 5, 0)
        
        data_points = [
            HeartRatePoint(start_time + timedelta(minutes=i), 70 + i)
            for i in range(4)  # 4 points (minimum is 5)
        ]
        
        session = HeartRateSession(
            start_time=start_time,
            end_time=end_time,
            data_points=data_points,
            format='csv',
            source_file='test.csv'
        )
        
        is_valid, errors = HeartRateDataValidator.validate_session(session)
        assert not is_valid
        assert any("Too few data points" in error for error in errors)
    
    def test_unrealistic_heart_rates(self):
        """Test validation of unrealistic heart rate values."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 5, 0)
        
        data_points = [
            HeartRatePoint(start_time + timedelta(minutes=i), 20 + i)  # Too low
            for i in range(6)
        ]
        
        session = HeartRateSession(
            start_time=start_time,
            end_time=end_time,
            data_points=data_points,
            format='csv',
            source_file='test.csv'
        )
        
        is_valid, errors = HeartRateDataValidator.validate_session(session)
        assert not is_valid
        assert any("Unrealistically low heart rate" in error for error in errors)
    
    def test_low_variation(self):
        """Test validation of session with low heart rate variation."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 5, 0)
        
        data_points = [
            HeartRatePoint(start_time + timedelta(minutes=i), 70)  # All same value
            for i in range(6)
        ]
        
        session = HeartRateSession(
            start_time=start_time,
            end_time=end_time,
            data_points=data_points,
            format='csv',
            source_file='test.csv'
        )
        
        is_valid, errors = HeartRateDataValidator.validate_session(session)
        assert not is_valid
        assert any("variation too low" in error for error in errors)


class TestHeartRateDataImporter:
    """Test HeartRateDataImporter class."""
    
    def test_csv_import(self):
        """Test importing CSV data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("timestamp,heart_rate,confidence\n")
            f.write("2024-01-15 10:00:00,72,0.95\n")
            f.write("2024-01-15 10:01:00,75,0.92\n")
            f.write("2024-01-15 10:02:00,78,0.89\n")
            temp_file = f.name
        
        try:
            session = HeartRateDataImporter.import_from_file(temp_file)
            
            assert session.format == 'csv'
            assert session.source_file == temp_file
            assert session.data_points_count == 3
            assert session.duration_minutes == 2
            assert session.average_heart_rate == 75.0
            assert session.min_heart_rate == 72.0
            assert session.max_heart_rate == 78.0
            
        finally:
            os.unlink(temp_file)
    
    def test_json_import(self):
        """Test importing JSON data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('''[
                {"timestamp": "2024-01-15T10:00:00", "heart_rate": 72, "confidence": 0.95},
                {"timestamp": "2024-01-15T10:01:00", "heart_rate": 75, "confidence": 0.92},
                {"timestamp": "2024-01-15T10:02:00", "heart_rate": 78, "confidence": 0.89}
            ]''')
            temp_file = f.name
        
        try:
            session = HeartRateDataImporter.import_from_file(temp_file)
            
            assert session.format == 'json'
            assert session.source_file == temp_file
            assert session.data_points_count == 3
            assert session.duration_minutes == 2
            assert session.average_heart_rate == 75.0
            
        finally:
            os.unlink(temp_file)
    
    def test_text_import(self):
        """Test importing text data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("2024-01-15 10:00:00,72,0.95\n")
            f.write("2024-01-15 10:01:00,75,0.92\n")
            f.write("2024-01-15 10:02:00,78,0.89\n")
            temp_file = f.name
        
        try:
            session = HeartRateDataImporter.import_from_file(temp_file)
            
            assert session.format == 'text'
            assert session.source_file == temp_file
            assert session.data_points_count == 3
            assert session.duration_minutes == 2
            
        finally:
            os.unlink(temp_file)
    
    def test_file_not_found(self):
        """Test importing from non-existent file."""
        with pytest.raises(FileNotFoundError):
            HeartRateDataImporter.import_from_file("nonexistent.csv")
    
    def test_unsupported_format(self):
        """Test importing from unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("some data")
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                HeartRateDataImporter.import_from_file(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_invalid_csv_data(self):
        """Test importing CSV with invalid data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("timestamp,heart_rate\n")
            f.write("invalid,data\n")  # Invalid timestamp and heart rate
            f.write("2024-01-15 10:00:00,72\n")  # Valid row
            temp_file = f.name
        
        try:
            session = HeartRateDataImporter.import_from_file(temp_file)
            
            # Should skip invalid row and only import valid one
            assert session.data_points_count == 1
            assert session.average_heart_rate == 72.0
            
        finally:
            os.unlink(temp_file)
