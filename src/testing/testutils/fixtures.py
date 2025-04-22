import pytest
from src.types import CustomStrEnum
from src.testing.mocks import get_mock_db


@pytest.fixture
def mock_db():
    """
    Fixture to create a mock database for testing.
    Automatically cleans up and deletes the database after the test.

    Usage:
    ```python
    def test_something(with_mock_db):
        assert True
    ```
    """
    with get_mock_db() as db:
        yield db
        db.close()


class Fixtures(CustomStrEnum):
    """Fixtures for the project."""

    MOCK_DB = "mock_db"
