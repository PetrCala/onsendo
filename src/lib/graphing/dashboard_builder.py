"""Dashboard builder for assembling multiple graphs into a single HTML file.

This module orchestrates data fetching, graph generation, and dashboard assembly.
"""

import os
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger
from sqlalchemy.orm import Session

from src.lib.graphing.base import DashboardConfig, DataSource, GraphDefinition
from src.lib.graphing.graph_generator import GraphGenerator
from src.paths import PATHS


class DashboardBuilder:
    """Builds interactive HTML dashboards from multiple graphs.

    This class handles:
    - Data fetching and preparation
    - Graph generation coordination
    - Dashboard assembly
    - File saving and browser opening
    """

    def __init__(self, session: Session):
        """Initialize the dashboard builder.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.generator = GraphGenerator()
        self._plotly = None
        self._make_subplots = None

    def _ensure_plotly(self):
        """Lazy import of Plotly libraries."""
        if self._plotly is None:
            # pylint: disable=import-outside-toplevel
            from plotly.subplots import make_subplots

            self._make_subplots = make_subplots
            self._plotly = True

    def build(self, config: DashboardConfig, auto_open: bool = True) -> Optional[str]:
        """Build a dashboard from configuration.

        Args:
            config: Dashboard configuration
            auto_open: Whether to open dashboard in browser

        Returns:
            Path to generated HTML file, or None if failed
        """
        self._ensure_plotly()

        # Fetch data for the data source
        data = self._fetch_data(config.data_source)
        if data is None or data.empty:
            logger.error(f"No data available for {config.data_source.value}")
            return None

        logger.info(
            f"Fetched {len(data)} records for {config.data_source.value} dashboard"
        )

        # Prepare data (add derived fields)
        data = self._prepare_data(data, config.data_source)

        # Filter to only graphs that can be generated with available data
        valid_graphs = self._filter_valid_graphs(config.graph_definitions, data)
        if not valid_graphs:
            logger.error("No valid graphs could be generated with available data")
            return None

        logger.info(f"Generating {len(valid_graphs)} graphs...")

        # Generate all graphs
        figures = []
        titles = []
        for graph_def in valid_graphs:
            try:
                fig = self.generator.generate(graph_def, data)
                if fig is not None:
                    figures.append(fig)
                    titles.append(graph_def.title)
                    logger.debug(f"Generated: {graph_def.title}")
            except Exception as e:
                logger.warning(f"Failed to generate '{graph_def.title}': {e}")
                continue

        if not figures:
            logger.error("No graphs were successfully generated")
            return None

        logger.info(f"Successfully generated {len(figures)} graphs")

        # Assemble dashboard
        dashboard = self._assemble_dashboard(figures, titles, config, data)

        # Save to file
        output_path = self._save_dashboard(dashboard, config)
        if output_path is None:
            return None

        logger.success(f"Dashboard saved to: {output_path}")

        # Open in browser
        if auto_open:
            self._open_in_browser(output_path)

        return output_path

    def _fetch_data(self, data_source: DataSource) -> Optional[pd.DataFrame]:
        """Fetch data from database based on data source.

        Args:
            data_source: Source of data to fetch

        Returns:
            DataFrame with fetched data, or None if failed
        """
        try:
            if data_source == DataSource.VISIT:
                return self._fetch_visit_data()
            elif data_source == DataSource.WEIGHT:
                return self._fetch_weight_data()
            elif data_source == DataSource.EXERCISE:
                return self._fetch_exercise_data()
            else:
                logger.error(f"Unsupported data source: {data_source}")
                return None
        except Exception as e:
            logger.error(f"Error fetching data for {data_source.value}: {e}")
            return None

    def _fetch_visit_data(self) -> pd.DataFrame:
        """Fetch onsen visit data from database."""
        # pylint: disable=import-outside-toplevel
        from src.db.models import OnsenVisit

        query = self.session.query(OnsenVisit)
        visits = query.all()

        if not visits:
            return pd.DataFrame()

        # Convert to DataFrame
        data = []
        for visit in visits:
            row = {
                "id": visit.id,
                "onsen_id": visit.onsen_id,
                "visit_time": visit.visit_time,
                "entry_fee_yen": visit.entry_fee_yen,
                "payment_method": visit.payment_method,
                "weather": visit.weather,
                "visited_with": visit.visited_with,
                "travel_mode": visit.travel_mode,
                "crowd_level": visit.crowd_level,
                "main_bath_type": visit.main_bath_type,
                "water_color": visit.water_color,
                "temperature_outside_celsius": visit.temperature_outside_celsius,
                "main_bath_temperature": visit.main_bath_temperature,
                "outdoor_bath_temperature": visit.outdoor_bath_temperature,
                "sauna_temperature": visit.sauna_temperature,
                "stay_length_minutes": visit.stay_length_minutes,
                "travel_time_minutes": visit.travel_time_minutes,
                "sauna_duration_minutes": visit.sauna_duration_minutes,
                "energy_level_change": visit.energy_level_change,
                "hydration_level": visit.hydration_level,
                "accessibility_rating": visit.accessibility_rating,
                "cleanliness_rating": visit.cleanliness_rating,
                "navigability_rating": visit.navigability_rating,
                "view_rating": visit.view_rating,
                "smell_intensity_rating": visit.smell_intensity_rating,
                "changing_room_cleanliness_rating": visit.changing_room_cleanliness_rating,
                "locker_availability_rating": visit.locker_availability_rating,
                "rest_area_rating": visit.rest_area_rating,
                "food_quality_rating": visit.food_quality_rating,
                "sauna_rating": visit.sauna_rating,
                "outdoor_bath_rating": visit.outdoor_bath_rating,
                "atmosphere_rating": visit.atmosphere_rating,
                "personal_rating": visit.personal_rating,
                "local_interaction_quality_rating": visit.local_interaction_quality_rating,
                "pre_visit_mood": visit.pre_visit_mood,
                "post_visit_mood": visit.post_visit_mood,
                "had_sauna": visit.had_sauna,
                "sauna_visited": visit.sauna_visited,
                "had_outdoor_bath": visit.had_outdoor_bath,
                "outdoor_bath_visited": visit.outdoor_bath_visited,
                "multi_onsen_day": visit.multi_onsen_day,
                "interacted_with_locals": visit.interacted_with_locals,
            }
            data.append(row)

        return pd.DataFrame(data)

    def _fetch_weight_data(self) -> pd.DataFrame:
        """Fetch weight measurement data (placeholder for future)."""
        # TODO: Implement when weight graphs are added
        logger.warning("Weight data fetching not yet implemented")
        return pd.DataFrame()

    def _fetch_exercise_data(self) -> pd.DataFrame:
        """Fetch exercise/activity data (placeholder for future)."""
        # TODO: Implement when exercise graphs are added
        logger.warning("Exercise data fetching not yet implemented")
        return pd.DataFrame()

    def _prepare_data(
        self, data: pd.DataFrame, data_source: DataSource
    ) -> pd.DataFrame:
        """Prepare data by adding derived fields.

        Args:
            data: Raw data
            data_source: Type of data

        Returns:
            DataFrame with derived fields added
        """
        if data_source == DataSource.VISIT:
            return self._prepare_visit_data(data)
        else:
            return data

    def _prepare_visit_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add derived fields to visit data.

        Derived fields:
        - visit_hour: Hour of day (0-23)
        - day_of_week: Day name (Monday, Tuesday, etc.)
        - month: Month name (January, February, etc.)
        - visits_per_day: Count of visits per day
        - sauna_usage_status: "Available & Used", "Available & Not Used", etc.
        - outdoor_bath_usage_status: Similar to sauna
        """
        prepared = data.copy()

        # Convert visit_time to datetime if not already
        if "visit_time" in prepared.columns:
            prepared["visit_time"] = pd.to_datetime(prepared["visit_time"])

            # Extract hour, day of week, month
            prepared["visit_hour"] = prepared["visit_time"].dt.hour
            prepared["day_of_week"] = prepared["visit_time"].dt.day_name()
            prepared["month"] = prepared["visit_time"].dt.month_name()
            prepared["visit_date"] = prepared["visit_time"].dt.date

            # Count visits per day
            daily_counts = prepared.groupby("visit_date").size()
            prepared["visits_per_day"] = prepared["visit_date"].map(daily_counts)

        # Sauna usage status
        if "had_sauna" in prepared.columns and "sauna_visited" in prepared.columns:
            prepared["sauna_usage_status"] = prepared.apply(
                lambda row: self._get_usage_status(
                    row["had_sauna"], row["sauna_visited"]
                ),
                axis=1,
            )

        # Outdoor bath usage status
        if (
            "had_outdoor_bath" in prepared.columns
            and "outdoor_bath_visited" in prepared.columns
        ):
            prepared["outdoor_bath_usage_status"] = prepared.apply(
                lambda row: self._get_usage_status(
                    row["had_outdoor_bath"], row["outdoor_bath_visited"]
                ),
                axis=1,
            )

        return prepared

    @staticmethod
    def _get_usage_status(had: Optional[bool], visited: Optional[bool]) -> str:
        """Determine usage status from availability and actual usage."""
        if had and visited:
            return "Available & Used"
        elif had and not visited:
            return "Available & Not Used"
        elif not had:
            return "Not Available"
        else:
            return "Unknown"

    def _filter_valid_graphs(
        self, graph_defs: list[GraphDefinition], data: pd.DataFrame
    ) -> list[GraphDefinition]:
        """Filter graph definitions to only those that can be generated.

        Args:
            graph_defs: All graph definitions
            data: Available data

        Returns:
            List of valid graph definitions
        """
        valid = []
        for graph_def in graph_defs:
            # Check if required field exists
            if graph_def.field not in data.columns:
                logger.debug(
                    f"Skipping '{graph_def.title}': field '{graph_def.field}' not in data"
                )
                continue

            # Check if secondary field exists (if required)
            if graph_def.field_y and graph_def.field_y not in data.columns:
                logger.debug(
                    f"Skipping '{graph_def.title}': field '{graph_def.field_y}' not in data"
                )
                continue

            # Check if color field exists (if specified)
            if graph_def.color_field and graph_def.color_field not in data.columns:
                logger.debug(
                    f"Skipping '{graph_def.title}': field '{graph_def.color_field}' not in data"
                )
                continue

            # Check if we have any non-null data for the field
            if data[graph_def.field].notna().sum() == 0:
                logger.debug(
                    f"Skipping '{graph_def.title}': no non-null data for '{graph_def.field}'"
                )
                continue

            valid.append(graph_def)

        return valid

    def _assemble_dashboard(  # pylint: disable=too-complex,too-many-locals
        self,
        figures: list,
        titles: list[str],
        config: DashboardConfig,
        data: pd.DataFrame,
    ):
        """Assemble multiple figures into a single dashboard.

        Complexity justified: Grid layout calculation and subplot type detection.

        Args:
            figures: List of Plotly figures
            titles: List of graph titles
            config: Dashboard configuration
            data: Original data (for summary stats)

        Returns:
            Combined Plotly figure
        """
        # pylint: disable=import-outside-toplevel
        import plotly.graph_objects as go

        # Calculate grid dimensions
        n_graphs = len(figures)
        cols = config.columns
        rows = (n_graphs + cols - 1) // cols  # Ceiling division

        # Determine subplot types for each position
        specs = []
        for i in range(rows):
            row_specs = []
            for j in range(cols):
                idx = i * cols + j
                if idx < n_graphs:
                    # Check trace type to determine subplot spec
                    fig = figures[idx]
                    if fig.data and isinstance(fig.data[0], go.Pie):
                        row_specs.append({"type": "pie"})
                    elif fig.data and isinstance(fig.data[0], go.Scatterpolar):
                        row_specs.append({"type": "polar"})
                    elif fig.data and isinstance(fig.data[0], go.Barpolar):
                        row_specs.append({"type": "polar"})
                    else:
                        row_specs.append({"type": "xy"})
                else:
                    # Empty subplot for grid alignment
                    row_specs.append({"type": "xy"})
            specs.append(row_specs)

        # Create subplot grid with specs
        # Calculate appropriate spacing based on grid size
        # vertical_spacing max = 1 / (rows - 1) for rows > 1
        if rows > 1:
            max_vertical_spacing = 1.0 / (rows - 1)
            vertical_spacing = min(0.04, max_vertical_spacing * 0.5)  # Reduced spacing
        else:
            vertical_spacing = 0.04

        # horizontal_spacing max = 1 / (cols - 1) for cols > 1
        if cols > 1:
            max_horizontal_spacing = 1.0 / (cols - 1)
            horizontal_spacing = min(0.08, max_horizontal_spacing * 0.8)
        else:
            horizontal_spacing = 0.08

        subplot_titles = titles
        fig = self._make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles,
            specs=specs,
            vertical_spacing=vertical_spacing,
            horizontal_spacing=horizontal_spacing,
        )

        # Add each figure to the grid and track pie charts
        pie_chart_indices = []
        for idx, graph_fig in enumerate(figures):
            row = idx // cols + 1
            col = idx % cols + 1

            # Track if this is a pie chart
            if graph_fig.data and isinstance(graph_fig.data[0], go.Pie):
                pie_chart_indices.append((row, col))

            # Add all traces from the graph to the subplot
            for trace in graph_fig.data:
                fig.add_trace(trace, row=row, col=col)

        # Make pie charts larger by updating their domain size
        # Pie charts in subplots use domain to control size - increase to fill cell better
        for row, col in pie_chart_indices:
            fig.update_traces(
                selector={"type": "pie", "row": row, "col": col},
                # Increase the hole size slightly for better proportions
                # and text positioning
                textposition="inside",
                textinfo="percent+label",
                insidetextorientation="radial",
            )

        # Adjust subplot title positioning to add space between title and chart
        fig.update_annotations(yshift=10)  # Push titles up by 10 pixels

        # Update layout with taller rows for better pie chart display
        dashboard_title = config.title
        if config.show_summary:
            summary = self._generate_summary_stats(data, config.data_source)
            dashboard_title = f"{config.title}<br><sub>{summary}</sub>"

        fig.update_layout(
            title_text=dashboard_title,
            title_font_size=24,
            showlegend=False,
            height=800 * rows,
            template="plotly_white",
            margin={
                "t": 200,
                "b": 200,
                "l": 50,
                "r": 50,
            },
        )

        return fig

    def _generate_summary_stats(
        self, data: pd.DataFrame, data_source: DataSource
    ) -> str:
        """Generate summary statistics text.

        Args:
            data: Data to summarize
            data_source: Type of data

        Returns:
            HTML-formatted summary text
        """
        if data_source == DataSource.VISIT:
            total = len(data)
            if "visit_time" in data.columns:
                date_range = f"{data['visit_time'].min().strftime('%Y-%m-%d')} to {data['visit_time'].max().strftime('%Y-%m-%d')}"
            else:
                date_range = "Unknown"

            return f"Total Visits: {total} | Date Range: {date_range}"
        else:
            return f"Total Records: {len(data)}"

    def _save_dashboard(self, dashboard, config: DashboardConfig) -> Optional[str]:
        """Save dashboard to HTML file.

        Args:
            dashboard: Plotly figure
            config: Dashboard configuration

        Returns:
            Path to saved file, or None if failed
        """
        try:
            # Ensure output directory exists
            os.makedirs(PATHS.GRAPHS_DIR, exist_ok=True)

            # Generate filename
            if config.output_filename:
                filename = config.output_filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{config.data_source.value}_dashboard_{timestamp}.html"

            output_path = os.path.join(PATHS.GRAPHS_DIR, filename)

            # Save to HTML
            dashboard.write_html(output_path)

            return output_path

        except Exception as e:
            logger.error(f"Error saving dashboard: {e}")
            return None

    def _open_in_browser(self, filepath: str):
        """Open HTML file in default browser.

        Args:
            filepath: Path to HTML file
        """
        try:
            # Convert to absolute path
            abs_path = Path(filepath).resolve()
            url = f"file://{abs_path}"

            # Open in browser
            webbrowser.open(url)
            logger.info("Dashboard opened in browser")

        except Exception as e:
            logger.warning(f"Could not open browser automatically: {e}")
            logger.info(f"Please open manually: {filepath}")
