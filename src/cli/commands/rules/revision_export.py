"""
Export rule revision data.
"""

import argparse
import json
import csv
import os
from src.db.conn import get_db
from src.db.models import RuleRevision
from src.config import get_database_config
from src.paths import PATHS


def export_revisions(args: argparse.Namespace) -> None:
    """
    Export rule revision data.

    Args:
        args: Command-line arguments containing:
            - version: Optional specific version to export (default: all)
            - format: Export format (json, csv, markdown)
            - output: Output file path
            - include_weekly_reviews: Include full weekly review data
    """
    # Get revisions to export
    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    with get_db(url=config.url) as db:
        if hasattr(args, "version") and args.version:
            revisions = [
                db.query(RuleRevision)
                .filter(RuleRevision.version_number == args.version)
                .first()
            ]
            if not revisions[0]:
                print(f"Error: Revision v{args.version} not found.")
                return
        else:
            revisions = (
                db.query(RuleRevision).order_by(RuleRevision.version_number.asc()).all()
            )

        if not revisions:
            print("No revisions found to export.")
            return

    # Determine format
    export_format = "json"
    if hasattr(args, "format") and args.format:
        export_format = args.format.lower()

    # Determine include weekly reviews
    include_weekly = False
    if hasattr(args, "include_weekly_reviews") and args.include_weekly_reviews:
        include_weekly = True

    # Determine output path
    if hasattr(args, "output") and args.output:
        output_path = args.output
    else:
        # Generate default output path
        timestamp = revisions[0].revision_date.strftime("%Y%m%d")
        if len(revisions) == 1:
            filename = f"rule_revision_v{revisions[0].version_number}_{timestamp}.{export_format}"
        else:
            filename = f"rule_revisions_export_{timestamp}.{export_format}"
        output_path = os.path.join(PATHS.OUTPUT_DIR, filename)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Export based on format
    if export_format == "json":
        export_json(revisions, output_path, include_weekly)
    elif export_format == "csv":
        export_csv(revisions, output_path, include_weekly)
    elif export_format == "markdown":
        export_markdown(revisions, output_path, include_weekly)
    else:
        print(
            f"Error: Unsupported format '{export_format}'. Use json, csv, or markdown."
        )
        return

    print(f"Exported {len(revisions)} revision(s) to: {output_path}")


def export_json(
    revisions: list[RuleRevision], output_path: str, include_weekly: bool
) -> None:
    """Export revisions to JSON format."""
    data = []

    for revision in revisions:
        revision_dict = {
            "version_number": revision.version_number,
            "revision_date": revision.revision_date.strftime("%Y-%m-%d"),
            "effective_date": revision.effective_date.strftime("%Y-%m-%d"),
            "week_start_date": revision.week_start_date,
            "week_end_date": revision.week_end_date,
            "adjustment": {
                "reason": revision.adjustment_reason,
                "description": revision.adjustment_description,
                "duration": revision.expected_duration,
                "health_safeguard": revision.health_safeguard_applied,
            },
            "sections_modified": json.loads(revision.sections_modified or "[]"),
            "revision_summary": revision.revision_summary,
            "markdown_file_path": revision.markdown_file_path,
        }

        if include_weekly:
            revision_dict["metrics"] = {
                "onsen_visits_count": revision.onsen_visits_count,
                "total_soaking_hours": revision.total_soaking_hours,
                "sauna_sessions_count": revision.sauna_sessions_count,
                "running_distance_km": revision.running_distance_km,
                "gym_sessions_count": revision.gym_sessions_count,
                "long_exercise_completed": revision.long_exercise_completed,
                "rest_days_count": revision.rest_days_count,
            }
            revision_dict["health"] = {
                "energy_level": revision.energy_level,
                "sleep_hours": revision.sleep_hours,
                "sleep_quality_rating": revision.sleep_quality_rating,
                "soreness_notes": revision.soreness_notes,
                "hydration_nutrition_notes": revision.hydration_nutrition_notes,
                "mood_mental_state": revision.mood_mental_state,
            }
            revision_dict["reflections"] = {
                "positive": revision.reflection_positive,
                "patterns": revision.reflection_patterns,
                "warnings": revision.reflection_warnings,
                "standout_onsens": revision.reflection_standout_onsens,
                "routine_notes": revision.reflection_routine_notes,
            }
            revision_dict["next_week"] = {
                "focus": revision.next_week_focus,
                "goals": revision.next_week_goals,
                "sauna_limit": revision.next_week_sauna_limit,
                "run_volume": revision.next_week_run_volume,
                "hike_destination": revision.next_week_hike_destination,
            }

        data.append(revision_dict)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def export_csv(
    revisions: list[RuleRevision], output_path: str, include_weekly: bool
) -> None:
    """Export revisions to CSV format."""
    fieldnames = [
        "version_number",
        "revision_date",
        "effective_date",
        "week_start_date",
        "week_end_date",
        "adjustment_reason",
        "adjustment_description",
        "expected_duration",
        "sections_modified",
        "revision_summary",
    ]

    if include_weekly:
        fieldnames.extend(
            [
                "onsen_visits_count",
                "total_soaking_hours",
                "sauna_sessions_count",
                "running_distance_km",
                "gym_sessions_count",
                "long_exercise_completed",
                "rest_days_count",
                "energy_level",
                "sleep_hours",
                "sleep_quality_rating",
            ]
        )

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for revision in revisions:
            row = {
                "version_number": revision.version_number,
                "revision_date": revision.revision_date.strftime("%Y-%m-%d"),
                "effective_date": revision.effective_date.strftime("%Y-%m-%d"),
                "week_start_date": revision.week_start_date,
                "week_end_date": revision.week_end_date,
                "adjustment_reason": revision.adjustment_reason,
                "adjustment_description": revision.adjustment_description,
                "expected_duration": revision.expected_duration,
                "sections_modified": revision.sections_modified,
                "revision_summary": revision.revision_summary,
            }

            if include_weekly:
                row.update(
                    {
                        "onsen_visits_count": revision.onsen_visits_count,
                        "total_soaking_hours": revision.total_soaking_hours,
                        "sauna_sessions_count": revision.sauna_sessions_count,
                        "running_distance_km": revision.running_distance_km,
                        "gym_sessions_count": revision.gym_sessions_count,
                        "long_exercise_completed": revision.long_exercise_completed,
                        "rest_days_count": revision.rest_days_count,
                        "energy_level": revision.energy_level,
                        "sleep_hours": revision.sleep_hours,
                        "sleep_quality_rating": revision.sleep_quality_rating,
                    }
                )

            writer.writerow(row)


def export_markdown(
    revisions: list[RuleRevision], output_path: str, include_weekly: bool
) -> None:
    """Export revisions to consolidated markdown format."""
    lines = []

    lines.append("# Rule Revisions Export")
    lines.append("")
    lines.append(f"**Exported:** {revisions[0].revision_date.strftime('%Y-%m-%d')}")
    lines.append(f"**Total Revisions:** {len(revisions)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for revision in revisions:
        lines.append(f"## Version {revision.version_number}")
        lines.append("")
        lines.append(f"**Date:** {revision.revision_date.strftime('%Y-%m-%d')}")
        lines.append(f"**Week:** {revision.week_start_date} → {revision.week_end_date}")
        lines.append("")

        lines.append("### Adjustment")
        lines.append(f"- **Reason:** {revision.adjustment_reason}")
        lines.append(f"- **Description:** {revision.adjustment_description}")
        lines.append(f"- **Duration:** {revision.expected_duration}")
        if revision.health_safeguard_applied:
            lines.append(f"- **Health Safeguard:** {revision.health_safeguard_applied}")
        lines.append("")

        try:
            sections = json.loads(revision.sections_modified or "[]")
            if sections:
                lines.append("### Sections Modified")
                lines.append(", ".join(f"§{s}" for s in sections))
                lines.append("")
        except json.JSONDecodeError:
            pass

        if include_weekly:
            lines.append("### Weekly Metrics")
            if revision.onsen_visits_count is not None:
                lines.append(f"- Onsen visits: {revision.onsen_visits_count}")
            if revision.sauna_sessions_count is not None:
                lines.append(f"- Sauna sessions: {revision.sauna_sessions_count}")
            if revision.running_distance_km is not None:
                lines.append(f"- Running: {revision.running_distance_km} km")
            lines.append("")

            lines.append("### Health")
            if revision.energy_level is not None:
                lines.append(f"- Energy: {revision.energy_level}/10")
            if revision.sleep_hours is not None:
                lines.append(f"- Sleep: {revision.sleep_hours}h")
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
