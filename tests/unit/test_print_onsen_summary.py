"""
Unit tests for the print_onsen_summary CLI command.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.cli.commands.print_onsen_summary import print_onsen_summary


class Args:
    """Simple args container to mimic argparse.Namespace."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@patch("src.cli.commands.print_onsen_summary.get_db")
@patch("loguru.logger.error")
def test_error_when_no_identifier(mock_error, mock_get_db):
    args = Args()
    print_onsen_summary(args)

    mock_error.assert_called_once()
    assert (
        "You must provide one of --onsen_id, --ban_number, or --name"
        in mock_error.call_args[0][0]
    )
    mock_get_db.assert_not_called()


@patch("src.cli.commands.print_onsen_summary.get_db")
@patch("loguru.logger.warning")
def test_priority_when_multiple_identifiers(mock_warning, mock_get_db):
    # Arrange DB and query mocks
    mock_session = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_session

    mock_onsen = MagicMock()
    mock_onsen.id = 42
    mock_onsen.ban_number = "B-001"
    mock_onsen.name = "Test"

    mock_session.query.return_value.filter.return_value.first.return_value = mock_onsen
    mock_session.query.return_value.filter.return_value.all.return_value = []

    # Act
    args = Args(onsen_id=42, ban_number="B-001", name="Test")
    with patch("builtins.print"):
        print_onsen_summary(args)

    # Assert: warning about multiple identifiers
    mock_warning.assert_called()
    # Priority: id should be used -> filter called with Onsen.id
    assert mock_session.query.return_value.filter.called


@patch("src.cli.commands.print_onsen_summary.get_db")
def test_summary_by_id_with_visits(mock_get_db):
    # Arrange session
    mock_session = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_session

    # Onsen record
    mock_onsen = MagicMock()
    mock_onsen.id = 1
    mock_onsen.ban_number = "BAN-123"
    mock_onsen.name = "Onsen Alpha"
    mock_onsen.region = "Beppu"
    mock_onsen.latitude = 33.2
    mock_onsen.longitude = 131.5
    mock_onsen.address = "Some address"
    mock_onsen.phone = "000-0000"
    mock_onsen.business_form = None
    mock_onsen.admission_fee = "400円"
    mock_onsen.usage_time = "8:00-17:00"
    mock_onsen.closed_days = "None"
    mock_onsen.spring_quality = "Sulfur"
    mock_onsen.private_bath = None
    mock_onsen.nearest_bus_stop = None
    mock_onsen.nearest_station = None
    mock_onsen.parking = None
    mock_onsen.remarks = None

    # Visits
    visit1 = MagicMock()
    visit1.visit_time = None
    visit1.personal_rating = 8
    visit1.cleanliness_rating = 7
    visit1.atmosphere_rating = 9

    visit2 = MagicMock()
    visit2.visit_time = None
    visit2.personal_rating = 6
    visit2.cleanliness_rating = 8
    visit2.atmosphere_rating = 7

    # Query chains
    mock_session.query.return_value.filter.return_value.first.return_value = mock_onsen
    # Second query for visits
    mock_session.query.return_value.filter.return_value.all.return_value = [
        visit1,
        visit2,
    ]

    args = Args(onsen_id=1)
    with patch("builtins.print") as mock_print:
        print_onsen_summary(args)

    # Verify core lines printed
    printed = "\n".join(str(c[0][0]) for c in mock_print.call_args_list)
    assert "ONSEN SUMMARY" in printed
    assert "Onsen Alpha" in printed
    assert "ID / BAN       : 1 / BAN-123" in printed
    assert "Visits         : 2" in printed
    assert "Avg personal   : 7.0 / 10" in printed  # (8+6)/2


@patch("src.cli.commands.print_onsen_summary.get_db")
@patch("loguru.logger.warning")
def test_summary_by_name_multiple_matches(mock_warning, mock_get_db):
    mock_session = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_session

    # Two matches, should pick the first ordered by id
    m1 = MagicMock()
    m1.id = 2
    m1.ban_number = "B-2"
    m1.name = "Same"
    m2 = MagicMock()
    m2.id = 5
    m2.ban_number = "B-5"
    m2.name = "Same"

    # For name search path, .first() is not used; .all() is used
    # Configure query().filter().order_by().all()
    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_order = mock_filter.order_by.return_value
    mock_order.all.return_value = [m1, m2]

    # Visits for chosen onsen id=2
    mock_session.query.return_value.filter.return_value.all.return_value = []

    args = Args(name="Same")
    with patch("builtins.print"):
        print_onsen_summary(args)

    mock_warning.assert_called()


@patch("src.cli.commands.print_onsen_summary.get_db")
@patch("loguru.logger.error")
def test_not_found_by_name(mock_error, mock_get_db):
    mock_session = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_session

    mock_query = mock_session.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_order = mock_filter.order_by.return_value
    mock_order.all.return_value = []

    args = Args(name="Does Not Exist")
    print_onsen_summary(args)

    mock_error.assert_called()
    assert "Onsen not found for name=Does Not Exist" in mock_error.call_args[0][0]
