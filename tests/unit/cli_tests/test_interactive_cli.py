"""
Unit tests for the interactive CLI functionality.

This module contains comprehensive unit tests for the add_visit_interactive function
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

from unittest.mock import patch, MagicMock
from src.cli.commands.visit.add import add_visit_interactive
from src.db.models import Onsen
from src.testing.mocks import (
    get_complete_flow_inputs,
    get_exercise_flow_inputs,
    get_invalid_onsen_retry_inputs,
    get_invalid_rating_retry_inputs,
    get_cancellation_inputs,
    get_minimal_flow_inputs,
)
import subprocess
import sys


class TestInteractiveAddVisit:
    """Test the add_visit_interactive function."""

    # TODO
    # - Rewrite common mock setup into fixtures

    @patch("builtins.input")
    @patch("src.cli.commands.visit.add.get_db")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_add_visit_interactive_complete_flow(
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
        mock_input.side_effect = get_complete_flow_inputs()

        add_visit_interactive()

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
    @patch("src.cli.commands.visit.add.get_db")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_add_visit_interactive_with_exercise(
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
        mock_input.side_effect = get_exercise_flow_inputs()

        # Call the function
        add_visit_interactive()

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
    @patch("src.cli.commands.visit.add.get_db")
    @patch("builtins.print")
    def test_add_visit_interactive_invalid_onsen_id(
        self, mock_print, mock_get_db, mock_input
    ):
        """Test handling of invalid onsen ID."""
        # Mock database setup
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock onsen query result - no onsen found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock user inputs with invalid onsen ID
        mock_input.side_effect = get_invalid_onsen_retry_inputs()

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
            add_visit_interactive()

            # Verify error message was printed for invalid onsen
            mock_print.assert_any_call("No onsen found with ID 999")

            # Verify subprocess was still called (after valid input)
            mock_subprocess.assert_called_once()

    @patch("builtins.input")
    @patch("src.cli.commands.visit.add.get_db")
    @patch("builtins.print")
    def test_add_visit_interactive_invalid_rating(
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
        mock_input.side_effect = get_invalid_rating_retry_inputs()

        # Mock subprocess
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0

            # Call the function
            add_visit_interactive()

            # Verify error message was printed for invalid rating
            mock_print.assert_any_call("Invalid input. Please try again.")

            # Verify subprocess was still called (after valid input)
            mock_subprocess.assert_called_once()

    @patch("builtins.input")
    @patch("src.cli.commands.visit.add.get_db")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_add_visit_interactive_user_cancels(
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
        mock_input.side_effect = get_cancellation_inputs()

        # Mock sys.exit
        with patch("sys.exit") as mock_exit:
            # Call the function
            add_visit_interactive()

            # Verify cancellation message was printed
            mock_print.assert_any_call("Visit recording cancelled.")

            # Verify sys.exit was called
            mock_exit.assert_called_once_with(0)

            # Verify subprocess was NOT called
            mock_subprocess.assert_not_called()

    @patch("builtins.input")
    @patch("src.cli.commands.visit.add.get_db")
    @patch("subprocess.run")
    @patch("builtins.print")
    def test_add_visit_interactive_subprocess_error(
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
        mock_input.side_effect = get_minimal_flow_inputs()

        # Mock sys.exit
        with patch("sys.exit") as mock_exit:
            # Call the function
            add_visit_interactive()

            # Verify error message was printed
            mock_print.assert_any_call(
                "❌ Error adding visit: Command 'onsendo add-visit' returned non-zero exit status 1."
            )
            mock_print.assert_any_call("Error details: Database error")

            # Verify sys.exit was called with error code
            mock_exit.assert_called_once_with(1)
