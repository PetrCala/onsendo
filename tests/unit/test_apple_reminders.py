"""Unit tests for Apple Reminders integration."""

import os
import platform
import tempfile
from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest

from src.lib.apple_reminders import (
    create_reminder,
    generate_reminder_script,
    is_reminders_available,
    format_onsen_details_for_reminder,
)


class TestIsRemindersAvailable:
    """Tests for is_reminders_available function."""

    def test_returns_true_on_macos(self):
        """Test that function returns True on macOS."""
        with patch('src.lib.apple_reminders.platform.system', return_value='Darwin'):
            assert is_reminders_available() is True

    def test_returns_false_on_linux(self):
        """Test that function returns False on Linux."""
        with patch('src.lib.apple_reminders.platform.system', return_value='Linux'):
            assert is_reminders_available() is False

    def test_returns_false_on_windows(self):
        """Test that function returns False on Windows."""
        with patch('src.lib.apple_reminders.platform.system', return_value='Windows'):
            assert is_reminders_available() is False


class TestCreateReminder:
    """Tests for create_reminder function."""

    def test_raises_error_on_non_macos(self):
        """Test that function raises RuntimeError on non-macOS platforms."""
        with patch('src.lib.apple_reminders.platform.system', return_value='Linux'):
            with pytest.raises(RuntimeError, match="only available on macOS"):
                create_reminder("Test", datetime.now())

    @pytest.mark.skipif(platform.system() != "Darwin", reason="Requires macOS")
    def test_creates_reminder_successfully(self):
        """Test that reminder is created successfully on macOS."""
        test_datetime = datetime(2025, 10, 28, 18, 30, 0)
        test_title = "Test Reminder"

        # Mock subprocess to avoid actual reminder creation
        with patch('src.lib.apple_reminders.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = create_reminder(test_title, test_datetime)

            assert result is True
            mock_run.assert_called_once()

            # Verify AppleScript contains correct date components
            call_args = mock_run.call_args[0][0]
            applescript = call_args[2]
            assert 'set year of theDate to 2025' in applescript
            assert 'set month of theDate to 10' in applescript
            assert 'set day of theDate to 28' in applescript
            assert 'set hours of theDate to 18' in applescript
            assert 'set minutes of theDate to 30' in applescript
            assert f'name:"{test_title}"' in applescript

    @pytest.mark.skipif(platform.system() != "Darwin", reason="Requires macOS")
    def test_handles_subprocess_error(self):
        """Test that function handles subprocess errors gracefully."""
        from subprocess import CalledProcessError

        test_datetime = datetime(2025, 10, 28, 18, 30, 0)

        with patch('src.lib.apple_reminders.subprocess.run') as mock_run:
            mock_run.side_effect = CalledProcessError(1, 'osascript', stderr='Error')

            result = create_reminder("Test", test_datetime)

            assert result is False

    @pytest.mark.skipif(platform.system() != "Darwin", reason="Requires macOS")
    def test_handles_timeout(self):
        """Test that function handles timeout gracefully."""
        from subprocess import TimeoutExpired

        test_datetime = datetime(2025, 10, 28, 18, 30, 0)

        with patch('src.lib.apple_reminders.subprocess.run') as mock_run:
            mock_run.side_effect = TimeoutExpired('osascript', 10)

            result = create_reminder("Test", test_datetime)

            assert result is False


class TestGenerateReminderScript:
    """Tests for generate_reminder_script function."""

    def test_skips_generation_on_non_macos(self):
        """Test that script generation is skipped on non-macOS platforms."""
        with patch('src.lib.apple_reminders.platform.system', return_value='Linux'):
            # Should not raise error, just log warning
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                generate_reminder_script("Test", datetime.now(), tmp.name)

                # File should not have been modified on non-macOS
                assert os.path.getsize(tmp.name) == 0
                os.unlink(tmp.name)

    @pytest.mark.skipif(platform.system() != "Darwin", reason="Requires macOS")
    def test_generates_script_with_correct_content(self):
        """Test that script is generated with correct content on macOS."""
        test_datetime = datetime(2025, 10, 28, 19, 30, 0)
        test_title = "Onsen recommendation 19:30"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.command', delete=False) as tmp:
            script_path = tmp.name

        try:
            generate_reminder_script(test_title, test_datetime, script_path)

            # Check file was created
            assert os.path.exists(script_path)

            # Check file is executable
            assert os.access(script_path, os.X_OK)

            # Check content
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert '#!/bin/bash' in content
            assert 'set year of theDate to 2025' in content
            assert 'set month of theDate to 10' in content
            assert 'set day of theDate to 28' in content
            assert 'set hours of theDate to 19' in content
            assert 'set minutes of theDate to 30' in content
            assert f'name:"{test_title}"' in content
            assert 'tell application "Reminders"' in content
            assert 'display notification' in content

        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)

    @pytest.mark.skipif(platform.system() != "Darwin", reason="Requires macOS")
    def test_handles_file_permission_error(self):
        """Test that function handles permission errors gracefully."""
        test_datetime = datetime(2025, 10, 28, 19, 30, 0)

        with patch('builtins.open', side_effect=PermissionError("No permission")):
            with pytest.raises(OSError):
                generate_reminder_script("Test", test_datetime, "/invalid/path/script.command")

    @pytest.mark.skipif(platform.system() != "Darwin", reason="Requires macOS")
    def test_script_contains_error_handling(self):
        """Test that generated script contains proper error handling."""
        test_datetime = datetime(2025, 10, 28, 19, 30, 0)
        test_title = "Test Reminder"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.command', delete=False) as tmp:
            script_path = tmp.name

        try:
            generate_reminder_script(test_title, test_datetime, script_path)

            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for error handling
            assert 'if [ $? -eq 0 ]' in content
            assert 'Success! Reminder created' in content
            assert 'Error: Failed to create reminder' in content
            assert 'sleep 3' in content

        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)

    @pytest.mark.skipif(platform.system() != "Darwin", reason="Requires macOS")
    def test_script_with_body_parameter(self):
        """Test that script is generated with body/notes parameter."""
        test_datetime = datetime(2025, 10, 28, 19, 30, 0)
        test_title = "Onsen Reminder"
        test_body = "Test onsen details\nWith multiple lines\nAnd special $characters"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.command', delete=False) as tmp:
            script_path = tmp.name

        try:
            generate_reminder_script(test_title, test_datetime, script_path, body=test_body)

            # Check file was created
            assert os.path.exists(script_path)

            # Check content includes body
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Body should be present and escaped properly
            assert 'body:' in content
            assert 'Test onsen details' in content

        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)


class TestFormatOnsenDetails:
    """Tests for format_onsen_details_for_reminder function."""

    def test_format_single_onsen(self):
        """Test formatting details for a single onsen recommendation."""
        # Create mock onsen and metadata
        class MockOnsen:
            def __init__(self):
                self.name = "Test Onsen"
                self.ban_number = "123"
                self.address = "123 Test St, Beppu"
                self.latitude = 33.2794
                self.longitude = 131.5006
                self.usage_time = "9:00-22:00"
                self.closed_days = "Monday"
                self.admission_fee = "100円"
                self.spring_quality = "Sodium Chloride"
                self.parking = "Available"
                self.remarks = "Test remark"

        metadata = {
            'distance_category': 'close',
            'is_available': True,
            'has_been_visited': False,
            'stay_restricted': False,
            'google_maps_link': 'https://maps.google.com/?q=33.2794,131.5006'
        }

        recommendations = [(MockOnsen(), 1.5, metadata)]
        result = format_onsen_details_for_reminder(recommendations, "Test Location")

        # Check key elements are present
        assert "Test Location" in result
        assert "Test Onsen" in result
        assert "BAN: 123" in result
        assert "1.5 km" in result
        assert "123 Test St, Beppu" in result
        assert "9:00-22:00" in result
        assert "100円" in result
        assert "Available" in result
        assert "https://maps.google.com" in result

    def test_format_multiple_onsens(self):
        """Test formatting details for multiple onsen recommendations."""
        class MockOnsen:
            def __init__(self, name, distance):
                self.name = name
                self.ban_number = "123"
                self.address = "Test Address"
                self.latitude = 33.2794
                self.longitude = 131.5006
                self.usage_time = "9:00-22:00"
                self.closed_days = None
                self.admission_fee = "100円"
                self.spring_quality = None
                self.parking = None
                self.remarks = None

        metadata = {
            'distance_category': 'close',
            'is_available': True,
            'has_been_visited': False,
            'stay_restricted': False,
            'google_maps_link': 'https://maps.google.com/?q=33.2794,131.5006'
        }

        recommendations = [
            (MockOnsen("Onsen 1", 1.0), 1.0, metadata),
            (MockOnsen("Onsen 2", 2.0), 2.0, metadata),
        ]

        result = format_onsen_details_for_reminder(recommendations, "Test Location")

        # Check both onsens are present
        assert "1. Onsen 1" in result
        assert "2. Onsen 2" in result
        assert "1.0 km" in result
        assert "2.0 km" in result
        # Check separator between onsens
        assert "---" in result

    def test_format_onsen_with_status_flags(self):
        """Test formatting with various status flags."""
        class MockOnsen:
            def __init__(self):
                self.name = "Test Onsen"
                self.ban_number = "123"
                self.address = "Test Address"
                self.latitude = 33.2794
                self.longitude = 131.5006
                self.usage_time = "9:00-22:00"
                self.closed_days = None
                self.admission_fee = "100円"
                self.spring_quality = None
                self.parking = None
                self.remarks = None

        metadata = {
            'distance_category': 'close',
            'is_available': False,
            'has_been_visited': True,
            'stay_restricted': True,
            'stay_restriction_notes': ['Guests only', 'Check-in required'],
            'google_maps_link': 'https://maps.google.com/?q=33.2794,131.5006'
        }

        recommendations = [(MockOnsen(), 1.5, metadata)]
        result = format_onsen_details_for_reminder(recommendations, "Test Location")

        # Check status indicators
        assert "Closed" in result
        assert "Visited" in result
        assert "Stay-restricted" in result
        assert "Guests only" in result
        assert "Check-in required" in result

    def test_format_empty_recommendations(self):
        """Test formatting with no recommendations."""
        result = format_onsen_details_for_reminder([], "Test Location")

        # Should still have header
        assert "Test Location" in result
