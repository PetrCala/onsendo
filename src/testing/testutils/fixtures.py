import os
import pytest
from src.types import CustomStrEnum
from src.testing.mocks import get_mock_db


@pytest.fixture
def mock_db(request: pytest.FixtureRequest):
    """
    Fixture to create a mock database for testing.
    Automatically cleans up and deletes the database after the test.

    Usage:
    ```python
    def test_something(with_mock_db):
        assert True
    ```
    """
    filename = request.param if hasattr(request, "param") else None

    with get_mock_db(filename) as db:
        yield db
        db.close()
        db_path = str(db.bind.url).replace("sqlite:///", "")
        if os.path.exists(db_path):
            os.remove(db_path)


class Fixtures(CustomStrEnum):
    """Fixtures for the project."""

    MOCK_DB = "mock_db"
