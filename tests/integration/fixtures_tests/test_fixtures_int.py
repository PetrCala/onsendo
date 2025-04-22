import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.testing.testutils import Integration


class TestMockDb(Integration):
    """Test the 'mock_db' fixture."""

    def test_object_type(self, mock_db):
        """Should be a SQLAlchemy session."""
        assert isinstance(mock_db, Session)

    def test_is_active(self, mock_db):
        """Should be active."""
        assert mock_db.is_active

    def test_simple_query(self, mock_db):
        """Should be able to run a simple query."""
        result = mock_db.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1

    def test_writes_to_db(self, mock_db):
        """Should be able to write to the database."""
        mock_db.execute(text("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"))
        mock_db.execute(
            text("INSERT INTO test (name) VALUES (:name)"), {"name": "test"}
        )
        result = mock_db.execute(text("SELECT * FROM test"))
        assert result.fetchone()[1] == "test"
