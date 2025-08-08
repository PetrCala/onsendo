"""
Unit tests for the interactive CLI functionality.

This module contains comprehensive unit tests for the add_visit_interactive function
that simulates user interactions and validates the complete flow of the interactive
onsen visit recording system.

Test Coverage:
- Complete interactive flow with all features enabled
- Conditional logic for exercise, sauna, and outdoor bath flows
- Input validation and error handling
- Navigation functionality (going back to previous answers)

Each test uses extensive mocking to simulate:
- User input via the input() function
- Database queries and responses
- Database operations (add, commit)
- Print statements for user feedback

The tests ensure that:
1. All user inputs are properly validated
2. Conditional logic works correctly (e.g., sauna questions only asked if sauna exists)
3. The final database operation is performed correctly with all arguments
4. Error handling works as expected
5. Navigation functionality works correctly
6. The user experience is smooth and informative
"""

from unittest.mock import patch, MagicMock
from src.cli.commands.visit.interactive import add_visit_interactive, InteractiveSession
from src.db.models import Onsen, OnsenVisit
from src.testing.mocks import (
    get_complete_flow_inputs,
    get_exercise_flow_inputs,
    get_invalid_onsen_retry_inputs,
    get_invalid_rating_retry_inputs,
    get_minimal_flow_inputs,
)
import sys


class TestInteractiveSession:
    """Test the InteractiveSession class functionality."""

    def test_session_initialization(self):
        """Test that InteractiveSession initializes correctly."""
        session = InteractiveSession()
        assert session.visit_data == {}
        assert session.history == []
        assert session.current_step == 0

    def test_add_to_history(self):
        """Test adding items to history."""
        session = InteractiveSession()
        session.add_to_history("test_field", "test_value", "test_prompt")

        assert len(session.history) == 1
        assert session.history[0] == ("test_field", "test_value", "test_prompt")
        assert session.current_step == 1
        assert session.visit_data == {}

    def test_get_previous_answer(self):
        """Test retrieving previous answers."""
        session = InteractiveSession()
        session.add_to_history("field1", "value1", "prompt1")
        session.add_to_history("field2", "value2", "prompt2")
        session.add_to_history("field1", "new_value1", "prompt1")

        # Should get the most recent value for field1
        assert session.get_previous_answer("field1") == "new_value1"
        assert session.get_previous_answer("field2") == "value2"
        assert session.get_previous_answer("nonexistent") is None

    def test_go_back_single_step(self):
        """Test going back one step."""
        session = InteractiveSession()
        session.add_to_history("field1", "value1", "prompt1")
        session.add_to_history("field2", "value2", "prompt2")
        session.visit_data["field1"] = "value1"
        session.visit_data["field2"] = "value2"

        steps_gone_back = session.go_back(1)

        assert steps_gone_back == 1
        assert session.current_step == 1
        assert len(session.history) == 1
        assert "field2" not in session.visit_data
        assert "field1" in session.visit_data

    def test_go_back_multiple_steps(self):
        """Test going back multiple steps."""
        session = InteractiveSession()
        session.add_to_history("field1", "value1", "prompt1")
        session.add_to_history("field2", "value2", "prompt2")
        session.add_to_history("field3", "value3", "prompt3")
        session.visit_data.update(
            {"field1": "value1", "field2": "value2", "field3": "value3"}
        )

        steps_gone_back = session.go_back(2)

        assert steps_gone_back == 2
        assert session.current_step == 1
        assert len(session.history) == 1
        assert "field1" in session.visit_data
        assert "field2" not in session.visit_data
        assert "field3" not in session.visit_data

    def test_go_back_beyond_history(self):
        """Test going back more steps than available."""
        session = InteractiveSession()
        session.add_to_history("field1", "value1", "prompt1")
        session.add_to_history("field2", "value2", "prompt2")
        session.visit_data.update({"field1": "value1", "field2": "value2"})

        steps_gone_back = session.go_back(5)

        assert steps_gone_back == 2
        assert session.current_step == 0
        assert len(session.history) == 0
        assert len(session.visit_data) == 0

    def test_go_back_zero_steps(self):
        """Test going back zero steps."""
        session = InteractiveSession()
        session.add_to_history("field1", "value1", "prompt1")
        session.visit_data["field1"] = "value1"

        steps_gone_back = session.go_back(0)

        assert steps_gone_back == 0
        assert session.current_step == 1
        assert len(session.history) == 1
        assert "field1" in session.visit_data


class TestInteractiveAddVisit:
    """Test the add_visit_interactive function."""

    # TODO
    # - Rewrite common mock setup into fixtures

    @patch("builtins.input")
    @patch("src.cli.commands.visit.interactive.get_db")
    @patch("builtins.print")
    def test_add_visit_interactive_complete_flow(
        self, mock_print, mock_get_db, mock_input
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

        # Mock visit object
        mock_visit = MagicMock()
        mock_visit.id = 123
        mock_visit.visit_time = "2024-01-01 12:00:00"
        mock_visit.personal_rating = 9

        # Mock user inputs for complete flow
        mock_input.side_effect = get_complete_flow_inputs()

        add_visit_interactive()

        # Verify database was queried for onsen (called twice: once for validation, once for summary)
        mock_db.query.assert_called_with(Onsen)
        assert mock_db.query.return_value.filter.call_count >= 1

        # Verify visit was added to database
        mock_db.add.assert_called_once()
        added_visit = mock_db.add.call_args[0][0]
        assert isinstance(added_visit, OnsenVisit)
        assert added_visit.onsen_id == 1

        # Verify commit was called
        mock_db.commit.assert_called_once()

        # Verify success message was printed
        mock_print.assert_any_call("✅ Successfully recorded visit to Test Onsen!")

    @patch("builtins.input")
    @patch("src.cli.commands.visit.interactive.get_db")
    @patch("builtins.print")
    def test_add_visit_interactive_with_exercise(
        self, mock_print, mock_get_db, mock_input
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

        # Mock user inputs with exercise
        mock_input.side_effect = get_exercise_flow_inputs()

        # Call the function
        add_visit_interactive()

        # Verify visit was added to database
        mock_db.add.assert_called_once()
        added_visit = mock_db.add.call_args[0][0]
        assert isinstance(added_visit, OnsenVisit)
        assert added_visit.onsen_id == 1
        assert added_visit.exercise_before_onsen is True
        assert added_visit.exercise_type == "running"
        assert added_visit.exercise_length_minutes == 30

        # Verify commit was called
        mock_db.commit.assert_called_once()

    @patch("builtins.input")
    @patch("src.cli.commands.visit.interactive.get_db")
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

        # Call the function
        add_visit_interactive()

        # Verify error message was printed for invalid onsen
        mock_print.assert_any_call("No onsen found with ID 999")

        # Verify visit was still added after valid input
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("builtins.input")
    @patch("src.cli.commands.visit.interactive.get_db")
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

        # Call the function
        add_visit_interactive()

        # Verify error message was printed for invalid rating
        mock_print.assert_any_call("Invalid input. Please try again.")

        # Verify visit was still added after valid input
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
