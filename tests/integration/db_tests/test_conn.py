from typing import Any
import pytest
from sqlalchemy.orm import Session
from src.db.conn import get_db, is_valid_url
from src.testing.mocks import get_mock_db_url


class TestIsValidUrl:
    """Test the is_valid_url function."""

    @pytest.mark.parametrize(
        "url", ["sqlite:///:memory:", "sqlite:///:memory:?check_same_thread=False"]
    )
    def test_valid_url(self, url: Any):
        """Should return True if the URL is valid."""
        assert is_valid_url(url)

    @pytest.mark.parametrize("url", [None, "invalid_url", 123])
    def test_invalid_url(self, url: Any):
        """Should return False if the URL is invalid."""
        assert not is_valid_url(url)


class TestGetDb:
    """Test the get_db function."""

    mock_url = get_mock_db_url()

    def test_get_db(self, mock_db):
        """Should return a valid SQLAlchemy session."""
        assert mock_db is not None
        assert isinstance(mock_db, Session)
        assert mock_db.is_active
