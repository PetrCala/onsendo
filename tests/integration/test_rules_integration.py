"""
Integration tests for rules management system.
"""

import pytest
from src.db.conn import get_db
from src.db.models import RuleRevision
from src.const import CONST
from datetime import datetime


@pytest.mark.integration
class TestRuleRevisionDatabase:
    """Test rule revision database operations."""

    def test_create_rule_revision(self):
        """Test creating a rule revision in the database."""
        with get_db(url=CONST.DATABASE_URL) as db:
            # Create a test revision
            revision = RuleRevision(
                version_number=999,  # Use high number to avoid conflicts
                revision_date=datetime(2025, 11, 10),
                effective_date=datetime(2025, 11, 11),
                week_start_date="2025-11-04",
                week_end_date="2025-11-10",
                onsen_visits_count=12,
                adjustment_reason="test",
                adjustment_description="Test revision",
                expected_duration="temporary",
                sections_modified="[]",
                revision_summary="Integration test revision",
                markdown_file_path="/tmp/test.md",
            )

            db.add(revision)
            db.commit()

            # Verify it was created
            retrieved = (
                db.query(RuleRevision)
                .filter(RuleRevision.version_number == 999)
                .first()
            )

            assert retrieved is not None
            assert retrieved.version_number == 999
            assert retrieved.onsen_visits_count == 12
            assert retrieved.adjustment_reason == "test"

            # Cleanup
            db.delete(retrieved)
            db.commit()

    def test_query_revisions(self):
        """Test querying revisions from database."""
        with get_db(url=CONST.DATABASE_URL) as db:
            # Get count of revisions
            count = db.query(RuleRevision).count()
            assert count >= 0

            # Try to get latest revision
            latest = (
                db.query(RuleRevision)
                .order_by(RuleRevision.version_number.desc())
                .first()
            )

            # If we have revisions, check their structure
            if latest:
                assert hasattr(latest, "version_number")
                assert hasattr(latest, "revision_date")
                assert hasattr(latest, "adjustment_reason")
