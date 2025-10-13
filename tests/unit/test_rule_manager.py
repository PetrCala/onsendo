"""
Unit tests for rule_manager module.
"""

from datetime import datetime

import pytest

from src.lib.rule_manager import (
    RuleParser,
    RuleDiffer,
    RuleMarkdownGenerator,
    RuleFileUpdater,
)
from src.paths import PATHS
from src.types.rules import (
    WeeklyReviewMetrics,
    HealthWellbeingData,
    ReflectionData,
    RuleAdjustmentContext,
    NextWeekPlan,
    RuleModification,
    RuleRevisionData,
)


class TestRuleParser:
    """Test the RuleParser class."""

    def test_parser_initialization(self):
        """Test that parser initializes with correct file path."""
        parser = RuleParser()
        assert parser.rules_file_path == PATHS.RULES_FILE

    def test_parse_returns_sections(self):
        """Test that parse method returns a list of sections."""
        parser = RuleParser()
        try:
            sections = parser.parse()
            assert isinstance(sections, list)
            assert len(sections) > 0
            # Check that sections have expected attributes
            if sections:
                assert hasattr(sections[0], "section_number")
                assert hasattr(sections[0], "section_title")
                assert hasattr(sections[0], "content")
        except FileNotFoundError:
            pytest.skip("Rules file not found - expected in development environment")

    def test_get_section_by_number(self):
        """Test getting a specific section by number."""
        parser = RuleParser()
        try:
            section = parser.get_section("1")
            if section:
                assert section.section_number == "1"
                assert section.section_title is not None
        except FileNotFoundError:
            pytest.skip("Rules file not found - expected in development environment")


class TestRuleDiffer:
    """Test the RuleDiffer class."""

    def test_generate_unified_diff(self):
        """Test unified diff generation."""
        differ = RuleDiffer()
        old_text = "Line 1\nLine 2\nLine 3"
        new_text = "Line 1\nLine 2 Modified\nLine 3"

        diff = differ.generate_unified_diff(old_text, new_text)
        assert isinstance(diff, str)
        assert "Line 2" in diff or "modified" in diff.lower()

    def test_side_by_side_comparison(self):
        """Test side-by-side comparison generation."""
        differ = RuleDiffer()
        old_text = "Original text"
        new_text = "Modified text"

        comparison = differ.generate_side_by_side_comparison(old_text, new_text, width=40)
        assert isinstance(comparison, str)
        assert "ORIGINAL" in comparison
        assert "MODIFIED" in comparison


class TestRuleMarkdownGenerator:
    """Test the RuleMarkdownGenerator class."""

    def test_generate_revision_markdown(self):
        """Test markdown generation for a revision."""
        generator = RuleMarkdownGenerator()

        # Create sample data
        metrics = WeeklyReviewMetrics(
            onsen_visits_count=12,
            total_soaking_hours=6.5,
            sauna_sessions_count=3,
        )

        health = HealthWellbeingData(
            energy_level=8,
            sleep_hours=7.5,
        )

        reflections = ReflectionData(
            reflection_positive="Good progress this week",
        )

        next_week = NextWeekPlan(
            next_week_focus="Recovery",
        )

        adjustment = RuleAdjustmentContext(
            adjustment_reason="schedule",
            adjustment_description="Reduced visits due to work",
            expected_duration="temporary",
        )

        modification = RuleModification(
            section_number="2",
            section_title="Visit Frequency and Timing",
            old_text="Old rule text",
            new_text="New rule text",
            rationale="Schedule adjustment",
        )

        revision_data = RuleRevisionData(
            version_number=1,
            revision_date=datetime(2025, 11, 10),
            effective_date=datetime(2025, 11, 11),
            week_start_date="2025-11-04",
            week_end_date="2025-11-10",
            metrics=metrics,
            health=health,
            reflections=reflections,
            next_week=next_week,
            adjustment=adjustment,
            modifications=[modification],
            revision_summary="Test revision",
            markdown_file_path="/tmp/test.md",
        )

        markdown = generator.generate_revision_markdown(revision_data)

        # Verify markdown content
        assert isinstance(markdown, str)
        assert "# Rule Revision v1" in markdown
        assert "2025-11-10" in markdown
        assert "Weekly Review Summary" in markdown
        assert "Rule Adjustment Context" in markdown
        assert "Modified Sections" in markdown


class TestRuleFileUpdater:
    """Test the RuleFileUpdater class (mock tests only)."""

    def test_updater_initialization(self):
        """Test that updater initializes correctly."""
        updater = RuleFileUpdater()
        assert updater.rules_file_path == PATHS.RULES_FILE
        assert updater.parser is not None
