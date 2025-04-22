from typing import Any
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from src import CONST
from src.db.conn import is_valid_url


class TestIsValidUrl:
    """Test the is_valid_url function."""

    @pytest.mark.parametrize(
        "url",
        [CONST.MOCK_DATABASE_URL, CONST.MOCK_DATABASE_URL + "?check_same_thread=False"],
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

    mock_url = CONST.MOCK_DATABASE_URL

    def test_get_db(self, mock_db):
        """Should return a valid SQLAlchemy session."""
        assert mock_db is not None
        assert isinstance(mock_db, Session)
        assert mock_db.is_active
