"""
Interactive browser for Strava activities.

Provides a full-featured terminal UI for browsing, downloading, importing,
and linking Strava activities to onsen visits.
"""

# pylint: disable=bad-builtin,too-complex

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from src.db.models import OnsenVisit
from src.lib.exercise_manager import ExerciseDataManager
from src.lib.heart_rate_manager import HeartRateDataManager
from src.lib.strava_client import StravaClient
from src.lib.strava_converter import (
    StravaFileExporter,
    StravaToExerciseConverter,
    StravaToHeartRateConverter,
)
from src.paths import PATHS
from src.types.strava import ActivityFilter, StravaActivityDetail, StravaActivitySummary


@dataclass
class BrowserState:
    """State management for interactive browser."""

    current_page: int = 1
    total_activities: int = 0
    filter: ActivityFilter = field(default_factory=ActivityFilter)
    selected_activities: list[int] = field(default_factory=list)
    activities_cache: dict[int, StravaActivitySummary] = field(default_factory=dict)
    current_page_activities: list[StravaActivitySummary] = field(default_factory=list)


class StravaActivityBrowser:
    """Interactive browser for Strava activities."""

    def __init__(self, client: StravaClient, db_session: Session):
        """Initialize browser with Strava client and database."""
        self.client = client
        self.db_session = db_session
        self.state = BrowserState()

    def run(self) -> None:
        """
        Start interactive browsing session.

        Main loop that handles user input and displays UI.
        """
        self._show_welcome()

        # Prompt for initial filters
        self.state.filter = self._prompt_filter_criteria()

        # Main browsing loop
        while True:
            try:
                # Fetch and display current page
                self._fetch_and_display_page(self.state.current_page)

                # Get user command
                command = input("\nCommand: ").strip().lower()

                if command == "q" or command == "quit":
                    print("\nExiting browser.")
                    break
                if command == "n" or command == "next":
                    self.state.current_page += 1
                elif command == "p" or command == "prev":
                    if self.state.current_page > 1:
                        self.state.current_page -= 1
                    else:
                        print("Already on first page")
                elif command == "f" or command == "filter":
                    self.state.filter = self._prompt_filter_criteria()
                    self.state.current_page = 1  # Reset to first page
                elif command == "s" or command == "select":
                    self._handle_selection()
                elif command == "d" or command == "details":
                    self._handle_details()
                elif command == "a" or command == "actions":
                    if not self.state.selected_activities:
                        print("No activities selected. Use 's' to select activities first.")
                    else:
                        self._handle_actions()
                elif command == "c" or command == "clear":
                    self.state.selected_activities = []
                    print("Selection cleared")
                else:
                    print(f"Unknown command: {command}")

            except KeyboardInterrupt:
                print("\n\nExiting browser.")
                break
            except Exception as e:
                logger.exception("Error in browser loop")
                print(f"\nError: {e}")
                print("Press Enter to continue...")
                input()

    def _show_welcome(self) -> None:
        """Display welcome screen and initial filter prompt."""
        print("\n" + "=" * 65)
        print(" " * 15 + "Strava Activity Browser")
        print("=" * 65)
        print("\nBrowse, download, and link your Strava activities to onsen visits.")
        print("\nCommands:")
        print("  [s]elect   - Select activities")
        print("  [d]etails  - View activity details")
        print("  [a]ctions  - Perform actions on selected activities")
        print("  [n]ext     - Next page")
        print("  [p]rev     - Previous page")
        print("  [f]ilter   - Change filter criteria")
        print("  [c]lear    - Clear selection")
        print("  [q]uit     - Exit browser")
        print("=" * 65)

    def _prompt_filter_criteria(self) -> ActivityFilter:
        """Interactive prompt for filter criteria."""
        print("\n--- Filter Criteria ---")

        # Date range
        days_input = input("Recent days (default 7, or 'all'): ").strip()
        if days_input and days_input.lower() != "all":
            try:
                days = int(days_input)
                date_from = datetime.now() - timedelta(days=days)
            except ValueError:
                print("Invalid number, using default 7 days")
                date_from = datetime.now() - timedelta(days=7)
        elif days_input.lower() == "all":
            date_from = None
        else:
            date_from = datetime.now() - timedelta(days=7)

        # Activity type
        activity_type_input = input(
            "Activity type (Run, Ride, Hike, or blank for all): "
        ).strip()
        activity_type = activity_type_input if activity_type_input else None

        # Heart rate filter
        hr_input = input("Only activities with heart rate? (y/N): ").strip().lower()
        has_heartrate = hr_input == "y" or hr_input == "yes"

        # Distance filter
        min_distance_input = input("Minimum distance in km (or blank): ").strip()
        min_distance_km = None
        if min_distance_input:
            try:
                min_distance_km = float(min_distance_input)
            except ValueError:
                print("Invalid distance, ignoring filter")

        # Page size
        page_size_input = input("Activities per page (default 10): ").strip()
        if page_size_input:
            try:
                page_size = int(page_size_input)
            except ValueError:
                page_size = 10
        else:
            page_size = 10

        return ActivityFilter(
            date_from=date_from,
            activity_type=activity_type,
            has_heartrate=has_heartrate if hr_input else None,
            min_distance_km=min_distance_km,
            page_size=page_size,
        )

    def _fetch_and_display_page(self, page: int) -> None:
        """Fetch activities for current page and display."""
        print(f"\nFetching page {page}...")

        # Update filter with current page
        self.state.filter.page = page

        # Fetch activities
        try:
            activities = self.client.list_activities(self.state.filter)
        except Exception as e:
            logger.exception("Failed to fetch activities")
            print(f"Error fetching activities: {e}")
            return

        if not activities:
            print("\nNo activities found matching your filters.")
            print("Try adjusting your filter criteria with 'f' command.")
            return

        # Update state
        self.state.current_page_activities = activities
        for activity in activities:
            self.state.activities_cache[activity.id] = activity

        # Display
        self._display_activity_list(activities)

    def _display_activity_list(
        self, activities: list[StravaActivitySummary]
    ) -> None:
        """
        Display formatted activity list.
        """
        page_size = self.state.filter.page_size
        start_num = (self.state.current_page - 1) * page_size + 1

        print("\n" + "┌" + "─" * 78 + "┐")
        print(f"│ Your Strava Activities (Page {self.state.current_page})" + " " * (78 - 38 - len(str(self.state.current_page))) + "│")
        print("├" + "─" * 78 + "┤")

        for i, activity in enumerate(activities):
            num = start_num + i
            selected = "✓" if activity.id in self.state.selected_activities else " "

            # Format activity name (truncate if too long)
            name = activity.name[:25] if len(activity.name) > 25 else activity.name
            name_padded = name.ljust(25)

            # Format date
            date_str = activity.start_date.strftime("%Y-%m-%d")

            # Format distance
            if activity.distance_km is not None:
                dist_str = f"{activity.distance_km:.1f}km"
            else:
                dist_str = "N/A"
            dist_padded = dist_str.ljust(8)

            # Format heart rate
            if activity.average_heartrate:
                hr_str = f"♥ {int(activity.average_heartrate)}bpm"
            else:
                hr_str = ""
            hr_padded = hr_str.ljust(10)

            # Check if already imported
            imported = self._check_if_already_imported(activity.id)
            imported_mark = " [IMP]" if imported else ""

            line = f"│ [{selected}] {num:2d}. {name_padded} {date_str}  {dist_padded} {hr_padded}{imported_mark}"
            # Pad to width
            line += " " * (79 - len(line)) + "│"
            print(line)

        print("├" + "─" * 78 + "┤")
        print("│ Commands: [s]elect | [d]etails | [n]ext | [p]rev | [f]ilter | [a]ctions  │")
        print("│           [c]lear selection | [q]uit" + " " * 40 + "│")
        print("└" + "─" * 78 + "┘")

        if self.state.selected_activities:
            print(f"\nSelected: {len(self.state.selected_activities)} activities")

    def _handle_selection(self) -> None:
        """Handle activity selection (single or multiple)."""
        selection = input(
            "Enter activity numbers to select/deselect (e.g., '1' or '1,2,3'): "
        ).strip()

        if not selection:
            return

        # Parse selection
        try:
            if "," in selection:
                nums = [int(n.strip()) for n in selection.split(",")]
            else:
                nums = [int(selection)]

            # Convert to activity IDs
            page_size = self.state.filter.page_size
            start_num = (self.state.current_page - 1) * page_size + 1

            for num in nums:
                # Get activity from current page
                index = num - start_num
                if 0 <= index < len(self.state.current_page_activities):
                    activity = self.state.current_page_activities[index]
                    if activity.id in self.state.selected_activities:
                        self.state.selected_activities.remove(activity.id)
                        print(f"Deselected: {activity.name}")
                    else:
                        self.state.selected_activities.append(activity.id)
                        print(f"Selected: {activity.name}")
                else:
                    print(f"Invalid number: {num}")

        except ValueError:
            print("Invalid input. Use numbers like '1' or '1,2,3'")

    def _handle_details(self) -> None:
        """Handle viewing activity details."""
        num_input = input("Enter activity number to view details: ").strip()

        try:
            num = int(num_input)

            # Convert to activity ID
            page_size = self.state.filter.page_size
            start_num = (self.state.current_page - 1) * page_size + 1
            index = num - start_num

            if 0 <= index < len(self.state.current_page_activities):
                activity_summary = self.state.current_page_activities[index]
                self._show_activity_details(activity_summary.id)
            else:
                print(f"Invalid number: {num}")

        except ValueError:
            print("Invalid input. Enter a number.")

    def _show_activity_details(self, activity_id: int) -> None:
        """
        Display detailed activity information.

        Fetches full activity data and streams summary.
        """
        print(f"\nFetching activity details...")

        try:
            activity = self.client.get_activity(activity_id)
        except Exception as e:
            logger.exception("Failed to fetch activity details")
            print(f"Error: {e}")
            return

        # Display details
        print("\n" + "=" * 65)
        print(f"Activity: {activity.name}")
        print("=" * 65)
        print(f"ID:           {activity.id}")
        print(f"Type:         {activity.activity_type} ({activity.sport_type})")
        print(f"Date:         {activity.start_date_local.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Timezone:     {activity.timezone}")

        if activity.description:
            print(f"Description:  {activity.description}")

        print("\n--- Metrics ---")
        if activity.distance_m:
            print(f"Distance:     {activity.distance_m / 1000:.2f} km")
        if activity.moving_time_s:
            mins = activity.moving_time_s // 60
            secs = activity.moving_time_s % 60
            print(f"Moving Time:  {mins}:{secs:02d}")
        if activity.elapsed_time_s:
            mins = activity.elapsed_time_s // 60
            secs = activity.elapsed_time_s % 60
            print(f"Elapsed Time: {mins}:{secs:02d}")
        if activity.total_elevation_gain_m:
            print(f"Elevation:    {activity.total_elevation_gain_m:.1f} m")
        if activity.calories:
            print(f"Calories:     {activity.calories}")

        print("\n--- Heart Rate ---")
        if activity.has_heartrate:
            print(f"Average:      {activity.average_heartrate:.0f} bpm")
            print(f"Max:          {activity.max_heartrate} bpm")
        else:
            print("No heart rate data")

        print("\n--- Performance ---")
        if activity.average_speed:
            print(f"Avg Speed:    {activity.average_speed * 3.6:.2f} km/h")
        if activity.max_speed:
            print(f"Max Speed:    {activity.max_speed * 3.6:.2f} km/h")
        if activity.average_cadence:
            print(f"Avg Cadence:  {activity.average_cadence:.0f}")
        if activity.average_watts:
            print(f"Avg Power:    {activity.average_watts:.0f} W")
        if activity.average_temp:
            print(f"Temperature:  {activity.average_temp}°C")

        print("\n--- Location ---")
        if activity.start_latlng:
            print(f"Start:        {activity.start_latlng[0]:.6f}, {activity.start_latlng[1]:.6f}")
        if activity.end_latlng:
            print(f"End:          {activity.end_latlng[0]:.6f}, {activity.end_latlng[1]:.6f}")

        print("=" * 65)

        # Check if already imported
        imported = self._check_if_already_imported(activity_id)
        if imported:
            print(f"\n✓ Already imported:")
            if imported.get("exercise_id"):
                print(f"  - Exercise session ID: {imported['exercise_id']}")
            if imported.get("hr_id"):
                print(f"  - Heart rate record ID: {imported['hr_id']}")

        input("\nPress Enter to continue...")

    def _handle_actions(self) -> None:
        """
        Handle actions for selected activities.

        Options:
        1. Download only (save to file)
        2. Download + import as exercise
        3. Download + import as heart rate
        4. Download + import + auto-link to visit
        5. Download + import + manual link to visit
        """
        print(f"\n{len(self.state.selected_activities)} activities selected")
        print("\n--- Actions ---")
        print("1. Download only (GPX/JSON/CSV files)")
        print("2. Download + Import as Exercise")
        print("3. Download + Import as Heart Rate")
        print("4. Download + Import + Auto-link to Visit")
        print("5. Download + Import + Manual link to Visit")
        print("0. Cancel")

        choice = input("\nChoice: ").strip()

        if choice == "0":
            return

        # Download format selection
        if choice in ["1", "2", "3", "4", "5"]:
            print("\nDownload formats:")
            print("1. GPX only")
            print("2. JSON only")
            print("3. HR CSV only")
            print("4. All formats")

            format_choice = input("Choice: ").strip()

            formats = []
            if format_choice == "1":
                formats = ["gpx"]
            elif format_choice == "2":
                formats = ["json"]
            elif format_choice == "3":
                formats = ["hr_csv"]
            elif format_choice == "4":
                formats = ["gpx", "json", "hr_csv"]
            else:
                print("Invalid choice")
                return

            # Process each selected activity
            for activity_id in self.state.selected_activities:
                activity = self.state.activities_cache.get(activity_id)
                if not activity:
                    print(f"Activity {activity_id} not in cache, skipping")
                    continue

                print(f"\nProcessing: {activity.name}")

                # Check if already imported
                imported = self._check_if_already_imported(activity_id)
                if imported and choice in ["2", "3", "4", "5"]:
                    print(f"  ⚠ Already imported (exercise: {imported.get('exercise_id')}, HR: {imported.get('hr_id')})")
                    skip = input("  Skip this activity? (Y/n): ").strip().lower()
                    if skip != "n":
                        continue

                # Download
                try:
                    file_paths = self._download_activity(activity_id, formats)
                    print(f"  ✓ Downloaded: {', '.join(file_paths.values())}")
                except Exception as e:
                    logger.exception("Failed to download activity")
                    print(f"  ✗ Download failed: {e}")
                    continue

                # Import if requested
                if choice in ["2", "4", "5"]:
                    # Import as exercise
                    try:
                        exercise_id = self._import_as_exercise_direct(activity_id)
                        print(f"  ✓ Imported as exercise (ID: {exercise_id})")

                        # Link to visit if requested
                        if choice in ["4", "5"]:
                            visit_id = self._prompt_visit_link(activity, choice == "4")
                            if visit_id:
                                exercise_mgr = ExerciseDataManager(self.db_session)
                                exercise_mgr.link_to_visit(exercise_id, visit_id)
                                print(f"  ✓ Linked to visit ID: {visit_id}")

                    except Exception as e:
                        logger.exception("Failed to import as exercise")
                        print(f"  ✗ Import failed: {e}")

                elif choice == "3":
                    # Import as heart rate
                    try:
                        hr_id = self._import_as_heart_rate_direct(activity_id)
                        if hr_id:
                            print(f"  ✓ Imported as heart rate (ID: {hr_id})")
                        else:
                            print(f"  ✗ No heart rate data available")
                    except Exception as e:
                        logger.exception("Failed to import as heart rate")
                        print(f"  ✗ Import failed: {e}")

            print("\n✓ Batch processing complete")
            input("\nPress Enter to continue...")

    def _download_activity(
        self, activity_id: int, formats: list[str]
    ) -> dict[str, str]:
        """
        Download activity in specified formats.

        Args:
            activity_id: Strava activity ID
            formats: List of formats ("gpx", "json", "hr_csv")

        Returns:
            Dict mapping format to file path
        """
        # Fetch activity and streams
        activity = self.client.get_activity(activity_id)
        streams = self.client.get_activity_streams(activity_id)

        # Smart format selection based on available data
        exportable_formats, skipped_formats = StravaFileExporter.recommend_formats(
            streams, formats
        )

        # Log skipped formats
        if skipped_formats:
            for fmt, reason in skipped_formats:
                logger.info(
                    f"Skipping {fmt} for activity {activity.name}: {reason}"
                )

        # Create output directory
        output_dir = PATHS.STRAVA_ACTIVITY_DIR.value
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Safe filename
        safe_name = "".join(
            c if c.isalnum() or c in (" ", "_", "-") else "_" for c in activity.name
        )
        safe_name = safe_name.strip()[:50]  # Limit length
        timestamp = activity.start_date_local.strftime("%Y%m%d_%H%M%S")
        base_filename = f"{timestamp}_{safe_name}_{activity_id}"

        file_paths = {}

        # Export in recommended formats
        if "gpx" in exportable_formats:
            gpx_path = Path(output_dir) / f"{base_filename}.gpx"
            StravaFileExporter.export_to_gpx(activity, streams, gpx_path)
            file_paths["gpx"] = str(gpx_path)

        if "json" in exportable_formats:
            json_path = Path(output_dir) / f"{base_filename}.json"
            StravaFileExporter.export_to_json(activity, streams, json_path)
            file_paths["json"] = str(json_path)

        if "hr_csv" in exportable_formats:
            csv_path = Path(output_dir) / f"{base_filename}_hr.csv"
            StravaFileExporter.export_hr_to_csv(
                activity, streams["heartrate"], streams.get("time"), csv_path
            )
            file_paths["hr_csv"] = str(csv_path)

        return file_paths

    def _import_as_exercise_direct(self, activity_id: int) -> int:
        """Import activity as exercise session directly from Strava API."""
        # Fetch activity and streams
        activity = self.client.get_activity(activity_id)
        streams = self.client.get_activity_streams(activity_id)

        # Convert to ExerciseSession
        session = StravaToExerciseConverter.convert(activity, streams)

        # Store in database
        manager = ExerciseDataManager(self.db_session)
        stored_session = manager.store_session(session)

        return stored_session.id

    def _import_as_heart_rate_direct(self, activity_id: int) -> Optional[int]:
        """Import activity as heart rate data directly from Strava API."""
        # Fetch activity and streams
        activity = self.client.get_activity(activity_id)
        streams = self.client.get_activity_streams(activity_id, ["heartrate", "time"])

        # Check if heart rate data exists
        if "heartrate" not in streams:
            return None

        # Convert to HeartRateSession
        hr_session = StravaToHeartRateConverter.convert(activity, streams["heartrate"])

        # Store in database
        hr_manager = HeartRateDataManager(self.db_session)
        stored_hr = hr_manager.store_session(hr_session)

        return stored_hr.id

    def _prompt_visit_link(
        self, activity: StravaActivitySummary, auto_suggest: bool
    ) -> Optional[int]:
        """Prompt user to link activity to a visit."""
        if auto_suggest:
            # Suggest visits based on activity time
            suggestions = self._suggest_visit_links(activity.start_date)
            if suggestions:
                return self._prompt_visit_selection(suggestions)

        # Manual ID entry
        visit_id_input = input("  Enter visit ID to link (or blank to skip): ").strip()
        if visit_id_input:
            try:
                return int(visit_id_input)
            except ValueError:
                print("  Invalid visit ID")
                return None

        return None

    def _suggest_visit_links(
        self, activity_time: datetime
    ) -> list[tuple[int, str]]:
        """
        Suggest onsen visits to link based on activity time.

        Searches for visits within ±2 hours of activity end time.

        Returns:
            List of (visit_id, description) tuples
        """
        # Search window: ±2 hours
        search_start = activity_time - timedelta(hours=2)
        search_end = activity_time + timedelta(hours=2)

        # Query visits
        visits = (
            self.db_session.query(OnsenVisit)
            .filter(OnsenVisit.visit_date >= search_start.date())
            .filter(OnsenVisit.visit_date <= search_end.date())
            .order_by(OnsenVisit.visit_date.desc(), OnsenVisit.visit_time.desc())
            .all()
        )

        suggestions = []
        for visit in visits:
            # Build description
            visit_datetime = datetime.combine(visit.visit_date, visit.visit_time or datetime.min.time())
            time_diff = abs((visit_datetime - activity_time).total_seconds() / 60)

            desc = f"Visit on {visit.visit_date} at {visit.visit_time or 'N/A'} ({time_diff:.0f} min from activity)"
            suggestions.append((visit.id, desc))

        return suggestions

    def _prompt_visit_selection(
        self, suggestions: list[tuple[int, str]]
    ) -> Optional[int]:
        """
        Interactive prompt for visit selection.

        Displays suggestions and allows manual ID entry.
        """
        print("\n  Suggested visits:")
        for i, (visit_id, desc) in enumerate(suggestions, 1):
            print(f"    {i}. [ID: {visit_id}] {desc}")

        choice = input("  Select number, enter visit ID, or blank to skip: ").strip()

        if not choice:
            return None

        try:
            num = int(choice)
            # Check if it's a suggestion number
            if 1 <= num <= len(suggestions):
                return suggestions[num - 1][0]
            # Otherwise treat as direct visit ID
            return num
        except ValueError:
            print("  Invalid input")
            return None

    def _check_if_already_imported(self, activity_id: int) -> Optional[dict]:
        """
        Check if activity already imported.

        Returns:
            Dict with exercise_id/hr_id if found, None otherwise
        """
        # For now, we don't have a direct mapping from Strava activity ID
        # This would require storing the Strava ID in the database models
        # Placeholder implementation
        return None
