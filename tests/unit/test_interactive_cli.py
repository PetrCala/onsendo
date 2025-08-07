"""
Unit tests for the interactive CLI functionality.

This module contains comprehensive unit tests for the interactive_add_visit function
that simulates user interactions and validates the complete flow of the interactive
onsen visit recording system.

Test Coverage:
- Complete interactive flow with all features enabled
- Conditional logic for exercise, sauna, and outdoor bath flows
- Input validation and error handling
- User cancellation scenarios
- Subprocess execution and error handling

Each test uses extensive mocking to simulate:
- User input via the input() function
- Database queries and responses
- Subprocess execution of the final CLI command
- Print statements for user feedback

The tests ensure that:
1. All user inputs are properly validated
2. Conditional logic works correctly (e.g., sauna questions only asked if sauna exists)
3. The final command is constructed correctly with all arguments
4. Error handling works as expected
5. The user experience is smooth and informative
"""

import pytest
from unittest.mock import patch, MagicMock, call
from src.cli.functions import interactive_add_visit
from src.db.models import Onsen
import subprocess
import sys


class TestInteractiveAddVisit:
    """Test the interactive_add_visit function."""

    @patch("builtins.input")
    @patch("src.cli.functions.get_db")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_interactive_add_visit_complete_flow(
        self, mock_print, mock_subprocess, mock_get_db, mock_input
    ):
        """Test the complete interactive flow with valid inputs."""
        # Mock database setup
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock onsen query result
        mock_onsen = MagicMock()
        mock_onsen.id = 1
        mock_onsen.name = "Test Onsen"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_onsen

        # Mock subprocess result
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Visit added successfully"

        # Mock user inputs for complete flow
        mock_input.side_effect = [
            "1",  # onsen_id
            "500",  # entry_fee_yen
            "cash",  # payment_method
            "",  # visit_time (use current time)
            "sunny",  # weather
            "afternoon",  # time_of_day
            "25.5",  # temperature_outside_celsius
            "60",  # stay_length_minutes
            "alone",  # visited_with
            "car",  # travel_mode
            "15",  # travel_time_minutes
            "n",  # exercise_before_onsen
            "8",  # accessibility_rating
            "9",  # cleanliness_rating
            "7",  # navigability_rating
            "8",  # view_rating
            "9",  # atmosphere_rating
            "open air",  # main_bath_type
            "42.0",  # main_bath_temperature
            "sulfur",  # main_bath_water_type
            "clear",  # water_color
            "6",  # smell_intensity_rating
            "8",  # changing_room_cleanliness_rating
            "7",  # locker_availability_rating
            "y",  # had_soap
            "y",  # had_sauna
            "y",  # sauna_visited
            "85.0",  # sauna_temperature
            "y",  # sauna_steam
            "15",  # sauna_duration_minutes
            "8",  # sauna_rating
            "y",  # had_outdoor_bath
            "y",  # outdoor_bath_visited
            "40.0",  # outdoor_bath_temperature
            "9",  # outdoor_bath_rating
            "y",  # had_rest_area
            "8",  # rest_area_rating
            "n",  # had_food_service
            "n",  # massage_chair_available
            "moderate",  # crowd_level
            "relaxed",  # pre_visit_mood
            "very relaxed",  # post_visit_mood
            "2",  # energy_level_change
            "7",  # hydration_level
            "n",  # multi_onsen_day
            "9",  # personal_rating
            "",  # heart_rate_data
            "y",  # confirm
        ]

        # Call the function
        interactive_add_visit()

        # Verify database was queried for onsen (called twice: once for validation, once for summary)
        mock_db.query.assert_called_with(Onsen)
        assert mock_db.query.return_value.filter.call_count >= 1

        # Verify subprocess was called with correct arguments
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        assert call_args[0][0][0] == "onsendo"
        assert call_args[0][0][1] == "add-visit"

        # Verify key arguments are present
        cmd_args = call_args[0][0]
        assert "--onsen_id" in cmd_args
        assert "--entry_fee_yen" in cmd_args
        assert "--payment_method" in cmd_args
        assert "--had_soap" in cmd_args
        assert "--had_sauna" in cmd_args
        assert "--sauna_visited" in cmd_args
        assert "--had_outdoor_bath" in cmd_args
        assert "--outdoor_bath_visited" in cmd_args
        assert "--had_rest_area" in cmd_args
        assert (
            "--multi_onsen_day" not in cmd_args
        )  # Should not be present since user said 'n'

        # Verify success message was printed
        mock_print.assert_any_call("✅ Visit successfully added!")

    @patch("builtins.input")
    @patch("src.cli.functions.get_db")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_interactive_add_visit_with_exercise(
        self, mock_print, mock_subprocess, mock_get_db, mock_input
    ):
        """Test the interactive flow when user exercised before onsen."""
        # Mock database setup
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock onsen query result
        mock_onsen = MagicMock()
        mock_onsen.id = 1
        mock_onsen.name = "Test Onsen"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_onsen

        # Mock subprocess result
        mock_subprocess.return_value.returncode = 0

        # Mock user inputs with exercise
        mock_input.side_effect = [
            "1",  # onsen_id
            "300",  # entry_fee_yen
            "card",  # payment_method
            "",  # visit_time
            "cloudy",  # weather
            "morning",  # time_of_day
            "20.0",  # temperature_outside_celsius
            "45",  # stay_length_minutes
            "friend",  # visited_with
            "walk",  # travel_mode
            "10",  # travel_time_minutes
            "y",  # exercise_before_onsen
            "running",  # exercise_type
            "30",  # exercise_length_minutes
            "7",  # accessibility_rating
            "8",  # cleanliness_rating
            "6",  # navigability_rating
            "7",  # view_rating
            "8",  # atmosphere_rating
            "indoor",  # main_bath_type
            "40.0",  # main_bath_temperature
            "salt",  # main_bath_water_type
            "brown",  # water_color
            "5",  # smell_intensity_rating
            "7",  # changing_room_cleanliness_rating
            "6",  # locker_availability_rating
            "n",  # had_soap
            "n",  # had_sauna
            "n",  # had_outdoor_bath
            "n",  # had_rest_area
            "n",  # had_food_service
            "n",  # massage_chair_available
            "quiet",  # crowd_level
            "stressed",  # pre_visit_mood
            "relaxed",  # post_visit_mood
            "3",  # energy_level_change
            "6",  # hydration_level
            "n",  # multi_onsen_day
            "8",  # personal_rating
            "",  # heart_rate_data
            "y",  # confirm
        ]

        # Call the function
        interactive_add_visit()

        # Verify subprocess was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args
        cmd_args = call_args[0][0]

        # Verify exercise-related arguments are present
        assert "--excercise_before_onsen" in cmd_args
        assert "--excercise_type" in cmd_args
        assert "--excercise_length_minutes" in cmd_args

        # Verify sauna/outdoor bath arguments are NOT present (user said no)
        assert "--had_sauna" not in cmd_args
        assert "--sauna_visited" not in cmd_args
        assert "--had_outdoor_bath" not in cmd_args
        assert "--outdoor_bath_visited" not in cmd_args

    @patch("builtins.input")
    @patch("src.cli.functions.get_db")
    @patch("builtins.print")
    def test_interactive_add_visit_invalid_onsen_id(
        self, mock_print, mock_get_db, mock_input
    ):
        """Test handling of invalid onsen ID."""
        # Mock database setup
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock onsen query result - no onsen found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock user inputs with invalid onsen ID
        mock_input.side_effect = [
            "999",  # invalid onsen_id
            "1",  # valid onsen_id (second attempt)
            "500",  # entry_fee_yen
            "cash",  # payment_method
            "",  # visit_time
            "sunny",  # weather
            "afternoon",  # time_of_day
            "25.0",  # temperature_outside_celsius
            "60",  # stay_length_minutes
            "alone",  # visited_with
            "car",  # travel_mode
            "15",  # travel_time_minutes
            "n",  # exercise_before_onsen
            "8",  # accessibility_rating
            "9",  # cleanliness_rating
            "7",  # navigability_rating
            "8",  # view_rating
            "9",  # atmosphere_rating
            "open air",  # main_bath_type
            "42.0",  # main_bath_temperature
            "sulfur",  # main_bath_water_type
            "clear",  # water_color
            "6",  # smell_intensity_rating
            "8",  # changing_room_cleanliness_rating
            "7",  # locker_availability_rating
            "y",  # had_soap
            "n",  # had_sauna
            "n",  # had_outdoor_bath
            "n",  # had_rest_area
            "n",  # had_food_service
            "n",  # massage_chair_available
            "moderate",  # crowd_level
            "relaxed",  # pre_visit_mood
            "relaxed",  # post_visit_mood
            "1",  # energy_level_change
            "7",  # hydration_level
            "n",  # multi_onsen_day
            "8",  # personal_rating
            "",  # heart_rate_data
            "y",  # confirm
        ]

        # Mock onsen for second attempt
        mock_onsen = MagicMock()
        mock_onsen.id = 1
        mock_onsen.name = "Test Onsen"

        # First call returns None, second call returns valid onsen
        # Need to provide enough values for all calls (validation + summary)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # First validation attempt
            mock_onsen,  # Second validation attempt
            mock_onsen,  # Summary display
        ]

        # Mock subprocess
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0

            # Call the function
            interactive_add_visit()

            # Verify error message was printed for invalid onsen
            mock_print.assert_any_call("No onsen found with ID 999")

            # Verify subprocess was still called (after valid input)
            mock_subprocess.assert_called_once()

    @patch("builtins.input")
    @patch("src.cli.functions.get_db")
    @patch("builtins.print")
    def test_interactive_add_visit_invalid_rating(
        self, mock_print, mock_get_db, mock_input
    ):
        """Test handling of invalid rating input."""
        # Mock database setup
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock onsen query result
        mock_onsen = MagicMock()
        mock_onsen.id = 1
        mock_onsen.name = "Test Onsen"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_onsen

        # Mock user inputs with invalid rating
        mock_input.side_effect = [
            "1",  # onsen_id
            "500",  # entry_fee_yen
            "cash",  # payment_method
            "",  # visit_time
            "sunny",  # weather
            "afternoon",  # time_of_day
            "25.0",  # temperature_outside_celsius
            "60",  # stay_length_minutes
            "alone",  # visited_with
            "car",  # travel_mode
            "15",  # travel_time_minutes
            "n",  # exercise_before_onsen
            "15",  # accessibility_rating (invalid - should be 1-10)
            "8",  # accessibility_rating (valid retry)
            "9",  # cleanliness_rating
            "7",  # navigability_rating
            "8",  # view_rating
            "9",  # atmosphere_rating
            "open air",  # main_bath_type
            "42.0",  # main_bath_temperature
            "sulfur",  # main_bath_water_type
            "clear",  # water_color
            "6",  # smell_intensity_rating
            "8",  # changing_room_cleanliness_rating
            "7",  # locker_availability_rating
            "y",  # had_soap
            "n",  # had_sauna
            "n",  # had_outdoor_bath
            "n",  # had_rest_area
            "n",  # had_food_service
            "n",  # massage_chair_available
            "moderate",  # crowd_level
            "relaxed",  # pre_visit_mood
            "relaxed",  # post_visit_mood
            "1",  # energy_level_change
            "7",  # hydration_level
            "n",  # multi_onsen_day
            "8",  # personal_rating
            "",  # heart_rate_data
            "y",  # confirm
        ]

        # Mock subprocess
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0

            # Call the function
            interactive_add_visit()

            # Verify error message was printed for invalid rating
            mock_print.assert_any_call("Invalid input. Please try again.")

            # Verify subprocess was still called (after valid input)
            mock_subprocess.assert_called_once()

    @patch("builtins.input")
    @patch("src.cli.functions.get_db")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_interactive_add_visit_user_cancels(
        self, mock_print, mock_subprocess, mock_get_db, mock_input
    ):
        """Test when user cancels the operation."""
        # Mock database setup
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock onsen query result
        mock_onsen = MagicMock()
        mock_onsen.id = 1
        mock_onsen.name = "Test Onsen"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_onsen

        # Mock user inputs with cancellation at the end
        mock_input.side_effect = [
            "1",  # onsen_id
            "500",  # entry_fee_yen
            "cash",  # payment_method
            "",  # visit_time
            "sunny",  # weather
            "afternoon",  # time_of_day
            "25.0",  # temperature_outside_celsius
            "60",  # stay_length_minutes
            "alone",  # visited_with
            "car",  # travel_mode
            "15",  # travel_time_minutes
            "n",  # exercise_before_onsen
            "8",  # accessibility_rating
            "9",  # cleanliness_rating
            "7",  # navigability_rating
            "8",  # view_rating
            "9",  # atmosphere_rating
            "open air",  # main_bath_type
            "42.0",  # main_bath_temperature
            "sulfur",  # main_bath_water_type
            "clear",  # water_color
            "6",  # smell_intensity_rating
            "8",  # changing_room_cleanliness_rating
            "7",  # locker_availability_rating
            "y",  # had_soap
            "n",  # had_sauna
            "n",  # had_outdoor_bath
            "n",  # had_rest_area
            "n",  # had_food_service
            "n",  # massage_chair_available
            "moderate",  # crowd_level
            "relaxed",  # pre_visit_mood
            "relaxed",  # post_visit_mood
            "1",  # energy_level_change
            "7",  # hydration_level
            "n",  # multi_onsen_day
            "8",  # personal_rating
            "",  # heart_rate_data
            "n",  # confirm (cancel)
        ]

        # Mock sys.exit
        with patch("sys.exit") as mock_exit:
            # Call the function
            interactive_add_visit()

            # Verify cancellation message was printed
            mock_print.assert_any_call("Visit recording cancelled.")

            # Verify sys.exit was called
            mock_exit.assert_called_once_with(0)

            # Verify subprocess was NOT called
            mock_subprocess.assert_not_called()

    @patch("builtins.input")
    @patch("src.cli.functions.get_db")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_interactive_add_visit_subprocess_error(
        self, mock_print, mock_subprocess, mock_get_db, mock_input
    ):
        """Test handling of subprocess execution error."""
        # Mock database setup
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock onsen query result
        mock_onsen = MagicMock()
        mock_onsen.id = 1
        mock_onsen.name = "Test Onsen"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_onsen

        # Mock subprocess error
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "onsendo add-visit", stderr="Database error"
        )

        # Mock user inputs
        mock_input.side_effect = [
            "1",  # onsen_id
            "500",  # entry_fee_yen
            "cash",  # payment_method
            "",  # visit_time
            "sunny",  # weather
            "afternoon",  # time_of_day
            "25.0",  # temperature_outside_celsius
            "60",  # stay_length_minutes
            "alone",  # visited_with
            "car",  # travel_mode
            "15",  # travel_time_minutes
            "n",  # exercise_before_onsen
            "8",  # accessibility_rating
            "9",  # cleanliness_rating
            "7",  # navigability_rating
            "8",  # view_rating
            "9",  # atmosphere_rating
            "open air",  # main_bath_type
            "42.0",  # main_bath_temperature
            "sulfur",  # main_bath_water_type
            "clear",  # water_color
            "6",  # smell_intensity_rating
            "8",  # changing_room_cleanliness_rating
            "7",  # locker_availability_rating
            "y",  # had_soap
            "n",  # had_sauna
            "n",  # had_outdoor_bath
            "n",  # had_rest_area
            "n",  # had_food_service
            "n",  # massage_chair_available
            "moderate",  # crowd_level
            "relaxed",  # pre_visit_mood
            "relaxed",  # post_visit_mood
            "1",  # energy_level_change
            "7",  # hydration_level
            "n",  # multi_onsen_day
            "8",  # personal_rating
            "",  # heart_rate_data
            "y",  # confirm
        ]

        # Mock sys.exit
        with patch("sys.exit") as mock_exit:
            # Call the function
            interactive_add_visit()

            # Verify error message was printed
            mock_print.assert_any_call(
                "❌ Error adding visit: Command 'onsendo add-visit' returned non-zero exit status 1."
            )
            mock_print.assert_any_call("Error details: Database error")

            # Verify sys.exit was called with error code
            mock_exit.assert_called_once_with(1)
