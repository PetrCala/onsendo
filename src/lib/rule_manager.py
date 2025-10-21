"""
Rule management system for Onsendo challenge ruleset.

Provides functionality for parsing, modifying, comparing, and generating
markdown files for rule revisions.
"""

import os
import re
import json
from typing import Optional
from datetime import datetime
from difflib import unified_diff

from src.paths import PATHS
from src.types.rules import (
    RuleSection,
    RuleModification,
    RuleRevisionData,
    RulesDiff,
)


class RuleParser:
    """Parse the Onsendo rules markdown file."""

    def __init__(self, rules_file_path: str = PATHS.RULES_FILE):
        """Initialize the parser with the rules file path."""
        self.rules_file_path = rules_file_path

    def parse(self) -> list[RuleSection]:
        """
        Parse the rules file and extract sections.

        Returns:
            List of RuleSection objects containing section metadata and content.
        """
        if not os.path.exists(self.rules_file_path):
            raise FileNotFoundError(f"Rules file not found: {self.rules_file_path}")

        with open(self.rules_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        sections = []
        # Pattern to match section headers like "## 1. Core Principles"
        section_pattern = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)

        matches = list(section_pattern.finditer(content))

        for i, match in enumerate(matches):
            section_number = match.group(1)
            section_title = match.group(2)
            start_pos = match.end()

            # Find end position (next section or end of file)
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                # For the last section, look for "### Version Control" or end of file
                version_control_match = re.search(
                    r"^### Version Control", content[start_pos:], re.MULTILINE
                )
                if version_control_match:
                    end_pos = start_pos + version_control_match.start()
                else:
                    end_pos = len(content)

            section_content = content[start_pos:end_pos].strip()

            # Extract individual rules (numbered list items)
            rules = self._extract_rules(section_content)

            sections.append(
                RuleSection(
                    section_number=section_number,
                    section_title=section_title,
                    content=section_content,
                    rules=rules,
                )
            )

        return sections

    def _extract_rules(self, section_content: str) -> list[str]:
        """Extract individual numbered rules from section content."""
        # Pattern for numbered list items (1., 2., etc.)
        rule_pattern = re.compile(r"^\d+\.\s+(.+?)(?=^\d+\.\s+|\Z)", re.MULTILINE | re.DOTALL)
        matches = rule_pattern.findall(section_content)
        return [match.strip() for match in matches]

    def get_section(self, section_number: str) -> Optional[RuleSection]:
        """Get a specific section by number."""
        sections = self.parse()
        for section in sections:
            if section.section_number == section_number:
                return section
        return None

    def get_full_content(self) -> str:
        """Get the full content of the rules file."""
        if not os.path.exists(self.rules_file_path):
            raise FileNotFoundError(f"Rules file not found: {self.rules_file_path}")

        with open(self.rules_file_path, "r", encoding="utf-8") as f:
            return f.read()


class RuleRevisionBuilder:
    """Build rule revision data from user input."""

    def __init__(self):
        """Initialize the builder."""
        self.parser = RuleParser()

    def get_next_version_number(self, database_url: Optional[str] = None) -> int:
        """
        Get the next version number based on existing revisions in the database.

        Args:
            database_url: Optional database URL. If not provided, uses CONST.DATABASE_URL.

        Returns:
            Next sequential version number.
        """
        from src.db.conn import get_db
        from src.db.models import RuleRevision
        from src.const import CONST

        url = database_url or CONST.DATABASE_URL
        with get_db(url=url) as db:
            max_version = db.query(RuleRevision.version_number).order_by(
                RuleRevision.version_number.desc()
            ).first()

            if max_version:
                return max_version[0] + 1
            return 1

    def build_modification(
        self,
        section_number: str,
        new_text: str,
        rationale: str,
    ) -> RuleModification:
        """
        Build a RuleModification object.

        Args:
            section_number: The section being modified
            new_text: The new text for the section
            rationale: Explanation for the change

        Returns:
            RuleModification object
        """
        section = self.parser.get_section(section_number)
        if not section:
            raise ValueError(f"Section {section_number} not found")

        return RuleModification(
            section_number=section_number,
            section_title=section.section_title,
            old_text=section.content,
            new_text=new_text,
            rationale=rationale,
        )


class RuleDiffer:
    """Generate diffs between rule versions."""

    def __init__(self):
        """Initialize the differ."""
        self.parser = RuleParser()

    def generate_diff(
        self,
        version_a: int,
        version_b: int,
        database_url: Optional[str] = None,
    ) -> RulesDiff:
        """
        Generate a diff between two rule versions.

        Args:
            version_a: First version number
            version_b: Second version number
            database_url: Optional database URL. If not provided, uses CONST.DATABASE_URL.

        Returns:
            RulesDiff object containing the differences
        """
        from src.db.conn import get_db
        from src.db.models import RuleRevision
        from src.const import CONST

        url = database_url or CONST.DATABASE_URL
        with get_db(url=url) as db:
            revision_a = (
                db.query(RuleRevision)
                .filter(RuleRevision.version_number == version_a)
                .first()
            )
            revision_b = (
                db.query(RuleRevision)
                .filter(RuleRevision.version_number == version_b)
                .first()
            )

            if not revision_a:
                raise ValueError(f"Version {version_a} not found")
            if not revision_b:
                raise ValueError(f"Version {version_b} not found")

            # Parse sections modified from JSON
            sections_a = json.loads(revision_a.sections_modified or "[]")
            sections_b = json.loads(revision_b.sections_modified or "[]")

            # Get unique sections across both versions
            all_sections = set(sections_a + sections_b)

            modifications = []
            # For each section, compare the rules at those versions
            # This is a simplified implementation - full implementation would
            # need to track the actual text at each version
            for section_num in all_sections:
                # This would require reading from the revision markdown files
                # or storing the full text in the database
                # For now, we'll create a placeholder
                pass

            return RulesDiff(
                version_a=version_a,
                version_b=version_b,
                sections_modified=list(all_sections),
                modifications=modifications,
            )

    def generate_unified_diff(self, old_text: str, new_text: str) -> str:
        """
        Generate a unified diff between two text blocks.

        Args:
            old_text: Original text
            new_text: Modified text

        Returns:
            Unified diff string
        """
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)

        diff = unified_diff(
            old_lines,
            new_lines,
            fromfile="original",
            tofile="modified",
            lineterm="",
        )

        return "".join(diff)

    def generate_side_by_side_comparison(
        self, old_text: str, new_text: str, width: int = 80
    ) -> str:
        """
        Generate a side-by-side comparison of two text blocks.

        Args:
            old_text: Original text
            new_text: Modified text
            width: Width of each column

        Returns:
            Formatted side-by-side comparison string
        """
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        max_lines = max(len(old_lines), len(new_lines))

        # Pad shorter list with empty strings
        old_lines += [""] * (max_lines - len(old_lines))
        new_lines += [""] * (max_lines - len(new_lines))

        result = []
        result.append("=" * (width * 2 + 5))
        result.append(f"{'ORIGINAL':<{width}} | {'MODIFIED':<{width}}")
        result.append("=" * (width * 2 + 5))

        for old_line, new_line in zip(old_lines, new_lines):
            # Truncate or pad lines to fit width
            old_display = old_line[:width].ljust(width) if old_line else " " * width
            new_display = new_line[:width].ljust(width) if new_line else " " * width

            marker = "|" if old_line != new_line else "│"
            result.append(f"{old_display} {marker} {new_display}")

        result.append("=" * (width * 2 + 5))
        return "\n".join(result)


class RuleMarkdownGenerator:
    """Generate markdown files for rule revisions."""

    def generate_revision_markdown(self, revision_data: RuleRevisionData) -> str:
        """
        Generate markdown content for a rule revision.

        Args:
            revision_data: Complete revision data

        Returns:
            Formatted markdown string
        """
        lines = []

        # Header
        lines.append(f"# Rule Revision v{revision_data.version_number}")
        lines.append("")
        lines.append(f"**Revision Date:** {revision_data.revision_date.strftime('%Y-%m-%d')}")
        lines.append(f"**Effective Date:** {revision_data.effective_date.strftime('%Y-%m-%d')}")
        lines.append(
            f"**Week Period:** {revision_data.week_start_date} → {revision_data.week_end_date}"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        # Weekly Review Summary
        lines.append("## Weekly Review Summary")
        lines.append("")
        lines.append("### Summary Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| ------ | ----- |")

        metrics = revision_data.metrics
        if metrics.onsen_visits_count is not None:
            lines.append(f"| Onsen visits | {metrics.onsen_visits_count} |")
        if metrics.total_soaking_hours is not None:
            lines.append(f"| Total soaking time (hrs) | {metrics.total_soaking_hours} |")
        if metrics.sauna_sessions_count is not None:
            lines.append(f"| Sauna sessions | {metrics.sauna_sessions_count} |")
        if metrics.running_distance_km is not None:
            lines.append(f"| Running distance (km) | {metrics.running_distance_km} |")
        if metrics.gym_sessions_count is not None:
            lines.append(f"| Gym sessions | {metrics.gym_sessions_count} |")
        if metrics.long_exercise_completed is not None:
            lines.append(
                f"| Long exercise session completed | {'Yes' if metrics.long_exercise_completed else 'No'} |"
            )
        if metrics.rest_days_count is not None:
            lines.append(f"| Rest days | {metrics.rest_days_count} |")

        lines.append("")

        # Health and Wellbeing
        lines.append("### Health and Wellbeing")
        lines.append("")
        health = revision_data.health
        if health.energy_level is not None:
            lines.append(f"- **Energy levels (1-10):** {health.energy_level}")
        if health.sleep_hours is not None or health.sleep_quality_rating:
            sleep_info = []
            if health.sleep_hours:
                sleep_info.append(f"{health.sleep_hours} hours")
            if health.sleep_quality_rating:
                sleep_info.append(health.sleep_quality_rating)
            lines.append(f"- **Sleep quality:** {' / '.join(sleep_info)}")
        if health.soreness_notes:
            lines.append(f"- **Soreness/pain/warnings:** {health.soreness_notes}")
        if health.hydration_nutrition_notes:
            lines.append(f"- **Hydration & nutrition:** {health.hydration_nutrition_notes}")
        if health.mood_mental_state:
            lines.append(f"- **Mood/mental state:** {health.mood_mental_state}")

        lines.append("")

        # Reflections
        lines.append("### Reflections")
        lines.append("")
        reflections = revision_data.reflections
        if reflections.reflection_positive:
            lines.append(f"**What went well:** {reflections.reflection_positive}")
            lines.append("")
        if reflections.reflection_patterns:
            lines.append(f"**Patterns/improvements:** {reflections.reflection_patterns}")
            lines.append("")
        if reflections.reflection_warnings:
            lines.append(f"**Warning signs:** {reflections.reflection_warnings}")
            lines.append("")
        if reflections.reflection_standout_onsens:
            lines.append(f"**Standout onsens:** {reflections.reflection_standout_onsens}")
            lines.append("")
        if reflections.reflection_routine_notes:
            lines.append(f"**Routine notes:** {reflections.reflection_routine_notes}")
            lines.append("")

        # Plans for Next Week
        lines.append("### Plans for Next Week")
        lines.append("")
        next_week = revision_data.next_week
        if next_week.next_week_focus:
            lines.append(f"- **Focus:** {next_week.next_week_focus}")
        if next_week.next_week_goals:
            lines.append(f"- **Goals:** {next_week.next_week_goals}")
        if next_week.next_week_sauna_limit is not None:
            lines.append(f"- **Sauna limit:** {next_week.next_week_sauna_limit}")
        if next_week.next_week_run_volume is not None:
            lines.append(f"- **Run volume:** {next_week.next_week_run_volume} km")
        if next_week.next_week_hike_destination:
            lines.append(f"- **Hike destination:** {next_week.next_week_hike_destination}")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Rule Adjustment Context
        lines.append("## Rule Adjustment Context")
        lines.append("")
        adjustment = revision_data.adjustment
        lines.append(f"**Reason for Adjustment:** {adjustment.adjustment_reason}")
        lines.append("")
        lines.append(f"**Description:** {adjustment.adjustment_description}")
        lines.append("")
        lines.append(f"**Expected Duration:** {adjustment.expected_duration}")
        lines.append("")
        if adjustment.health_safeguard_applied:
            lines.append(f"**Health Safeguard:** {adjustment.health_safeguard_applied}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # Modified Sections
        lines.append("## Modified Sections")
        lines.append("")

        for modification in revision_data.modifications:
            lines.append(f"### Section {modification.section_number}: {modification.section_title}")
            lines.append("")
            lines.append("**Previous Rule:**")
            lines.append("```")
            lines.append(modification.old_text)
            lines.append("```")
            lines.append("")
            lines.append("**New Rule:**")
            lines.append("```")
            lines.append(modification.new_text)
            lines.append("```")
            lines.append("")
            lines.append(f"**Rationale:** {modification.rationale}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Version Control
        lines.append("## Version Control")
        lines.append("")
        if revision_data.version_number > 1:
            lines.append(f"- **Previous version:** v{revision_data.version_number - 1}")
        lines.append(f"- **This version:** v{revision_data.version_number}")
        lines.append("")

        return "\n".join(lines)

    def save_revision_markdown(
        self, revision_data: RuleRevisionData, output_path: str
    ) -> None:
        """
        Generate and save revision markdown to a file.

        Args:
            revision_data: Complete revision data
            output_path: Path to save the markdown file
        """
        markdown_content = self.generate_revision_markdown(revision_data)

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)


class RuleFileUpdater:
    """Update the main onsendo-rules.md file with new rule versions."""

    def __init__(self, rules_file_path: str = PATHS.RULES_FILE):
        """Initialize the updater with the rules file path."""
        self.rules_file_path = rules_file_path
        self.parser = RuleParser(rules_file_path)

    def update_section(self, section_number: str, new_content: str) -> None:
        """
        Update a specific section in the rules file.

        Args:
            section_number: The section number to update
            new_content: The new content for the section
        """
        full_content = self.parser.get_full_content()

        # Find the section to update
        section_pattern = re.compile(
            rf"^## {re.escape(section_number)}\. (.+?)$.*?(?=^## \d+\.|^### Version Control|\Z)",
            re.MULTILINE | re.DOTALL,
        )

        def replace_section(match):
            section_title = match.group(1)
            return f"## {section_number}. {section_title}\n\n{new_content}\n\n"

        updated_content = section_pattern.sub(replace_section, full_content, count=1)

        # Write back to file
        with open(self.rules_file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

    def update_version_control_section(
        self, version_number: int, revision_date: datetime, summary: str
    ) -> None:
        """
        Update the version control section at the bottom of the rules file.

        Args:
            version_number: The new version number
            revision_date: Date of the revision
            summary: Brief summary of changes
        """
        full_content = self.parser.get_full_content()

        # Find or create the Version Control section
        version_control_pattern = re.compile(
            r"^### Version Control\s*$(.*?)(?=^##|\Z)",
            re.MULTILINE | re.DOTALL,
        )

        new_entry = f"- **Version {version_number}:** {revision_date.strftime('%Y-%m-%d')} - {summary}\n"

        match = version_control_pattern.search(full_content)
        if match:
            # Version Control section exists, add new entry
            existing_entries = match.group(1).strip()
            if existing_entries:
                new_entries = f"{existing_entries}\n{new_entry}"
            else:
                new_entries = new_entry

            updated_section = f"### Version Control\n\n{new_entries}\n"
            updated_content = version_control_pattern.sub(
                updated_section, full_content, count=1
            )
        else:
            # Version Control section doesn't exist, create it
            version_control_section = f"\n---\n\n### Version Control\n\n{new_entry}\n"
            updated_content = full_content.rstrip() + version_control_section

        # Write back to file
        with open(self.rules_file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

    def apply_modifications(
        self,
        modifications: list[RuleModification],
        version_number: int,
        revision_date: datetime,
        summary: str
    ) -> None:
        """
        Apply multiple modifications to the rules file.

        Args:
            modifications: List of RuleModification objects
            version_number: Version number for this revision
            revision_date: Date of the revision
            summary: Brief summary of changes
        """
        # Apply all section updates
        for modification in modifications:
            self.update_section(modification.section_number, modification.new_text)

        # Update version control section
        self.update_version_control_section(version_number, revision_date, summary)
