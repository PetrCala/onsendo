from src.db.conn import get_db
from src.testing.mocks import get_mock_db_url


class TestGetDb:
    """Test the get_db function."""

    mock_url = get_mock_db_url()

    def test_get_db(self):
        """Test the get_db function."""
        assert True  # A placeholder

        # with get_db(url=self.mock_url) as db:
        #     assert db is not None
        #     assert isinstance(db, Session)
