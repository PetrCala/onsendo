"""Core graph generation logic.

This module generates individual Plotly figures from GraphDefinition objects.
"""

import warnings
from typing import Optional

import pandas as pd
from loguru import logger
import plotly.graph_objects as go

from src.lib.graphing.base import GraphDefinition, GraphType


class GraphGenerator:
    """Generates Plotly figures from graph definitions.

    This class handles all graph types and data transformations needed
    to create high-quality, interactive visualizations.
    """

    def __init__(self):
        """Initialize the graph generator.

        Uses lazy imports to avoid loading Plotly at module import time.
        """
        self._plotly = None
        self._px = None
        self._go = None

    def _ensure_plotly(self):
        """Lazy import of Plotly libraries."""
        if self._plotly is None:
            # pylint: disable=import-outside-toplevel
            import plotly.express as px
            import plotly.graph_objects as go

            self._px = px
            self._go = go
            self._plotly = True

    def generate(  # pylint: disable=too-complex,too-many-return-statements
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> Optional["go.Figure"]:
        """Generate a Plotly figure from a graph definition.

        Complexity justified: Dispatcher function for multiple graph types.

        Args:
            graph_def: Graph definition specifying what to generate
            data: DataFrame containing the data to visualize

        Returns:
            Plotly Figure object, or None if generation failed

        Raises:
            ValueError: If required fields are missing from data
        """
        self._ensure_plotly()

        # Validate required fields exist in data
        self._validate_fields(graph_def, data)

        # Apply filters if specified
        if graph_def.filters:
            data = self._apply_filters(data, graph_def.filters)

        # Check if we have data after filtering
        if data.empty:
            logger.warning(
                f"No data available for graph '{graph_def.title}' after filtering"
            )
            return None

        # Suppress FutureWarnings from Plotly (common with newer pandas versions)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)

            # Generate graph based on type
            try:
                if graph_def.graph_type == GraphType.HISTOGRAM:
                    return self._generate_histogram(graph_def, data)
                elif graph_def.graph_type == GraphType.PIE:
                    return self._generate_pie(graph_def, data)
                elif graph_def.graph_type == GraphType.BAR:
                    return self._generate_bar(graph_def, data)
                elif graph_def.graph_type == GraphType.SCATTER:
                    return self._generate_scatter(graph_def, data)
                elif graph_def.graph_type == GraphType.BOX:
                    return self._generate_box(graph_def, data)
                elif graph_def.graph_type == GraphType.LINE:
                    return self._generate_line(graph_def, data)
                elif graph_def.graph_type == GraphType.RADAR:
                    return self._generate_radar(graph_def, data)
                elif graph_def.graph_type == GraphType.HEATMAP:
                    return self._generate_heatmap(graph_def, data)
                elif graph_def.graph_type == GraphType.VIOLIN:
                    return self._generate_violin(graph_def, data)
                elif graph_def.graph_type == GraphType.POLAR:
                    return self._generate_polar(graph_def, data)
                else:
                    logger.error(f"Unsupported graph type: {graph_def.graph_type}")
                    return None

            except Exception as e:
                logger.error(
                    f"Error generating graph '{graph_def.title}': {e}", exc_info=True
                )
                return None

    def _validate_fields(self, graph_def: GraphDefinition, data: pd.DataFrame):
        """Validate that required fields exist in the data.

        Args:
            graph_def: Graph definition
            data: DataFrame to validate

        Raises:
            ValueError: If required field is missing
        """
        required_fields = [graph_def.field]
        if graph_def.field_y:
            required_fields.append(graph_def.field_y)
        if graph_def.color_field:
            required_fields.append(graph_def.color_field)

        missing = [f for f in required_fields if f not in data.columns]
        if missing:
            raise ValueError(
                f"Missing required fields for graph '{graph_def.title}': {missing}"
            )

    def _apply_filters(self, data: pd.DataFrame, filters: dict) -> pd.DataFrame:
        """Apply filters to the data.

        Args:
            data: DataFrame to filter
            filters: Dictionary of field -> value filters

        Returns:
            Filtered DataFrame
        """
        filtered = data.copy()
        for field, value in filters.items():
            if field in filtered.columns:
                filtered = filtered[filtered[field] == value]
        return filtered

    def _generate_histogram(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a histogram."""
        # Remove null values
        clean_data = data[data[graph_def.field].notna()]

        fig = self._px.histogram(
            clean_data,
            x=graph_def.field,
            nbins=graph_def.bins,
            color=graph_def.color_field,
            title=graph_def.title,
            color_discrete_sequence=self._px.colors.qualitative.Set2,
        )

        # Add KDE overlay if requested
        if graph_def.show_kde:
            self._add_kde_overlay(fig, clean_data[graph_def.field])

        fig.update_layout(showlegend=True if graph_def.color_field else False)
        return fig

    def _generate_pie(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a pie chart."""
        # Count occurrences of each value
        value_counts = data[graph_def.field].value_counts()

        # Apply limit if specified
        if graph_def.limit:
            value_counts = value_counts.head(graph_def.limit)

        fig = self._px.pie(
            values=value_counts.values,
            names=value_counts.index,
            title=graph_def.title,
            color_discrete_sequence=self._px.colors.qualitative.Set3,
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")
        return fig

    def _generate_bar(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a bar chart."""
        # If we have aggregation, group by field and aggregate
        if graph_def.aggregation:
            if graph_def.field_y:
                grouped = data.groupby(graph_def.field)[graph_def.field_y].agg(
                    graph_def.aggregation
                )
            else:
                grouped = data[graph_def.field].value_counts()

            plot_data = pd.DataFrame({"x": grouped.index, "y": grouped.values})
        else:
            # Simple value counts
            value_counts = data[graph_def.field].value_counts()

            # Apply limit if specified
            if graph_def.limit:
                value_counts = value_counts.head(graph_def.limit)

            # Sort if specified
            if graph_def.sort_by == "value":
                value_counts = value_counts.sort_values(ascending=False)
            elif graph_def.sort_by == "name":
                value_counts = value_counts.sort_index()

            plot_data = pd.DataFrame(
                {"x": value_counts.index, "y": value_counts.values}
            )

        fig = self._px.bar(
            plot_data,
            x="x",
            y="y",
            title=graph_def.title,
            color_discrete_sequence=[self._px.colors.qualitative.Set2[0]],
        )

        fig.update_layout(xaxis_title=graph_def.field, yaxis_title="Count")
        return fig

    def _generate_scatter(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a scatter plot."""
        # Remove rows with null values in either field
        clean_data = data[
            data[graph_def.field].notna() & data[graph_def.field_y].notna()
        ]

        fig = self._px.scatter(
            clean_data,
            x=graph_def.field,
            y=graph_def.field_y,
            color=graph_def.color_field,
            title=graph_def.title,
            color_discrete_sequence=self._px.colors.qualitative.Set2,
        )

        return fig

    def _generate_box(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a box plot."""
        # If we have a color field, use it for grouping
        if graph_def.color_field:
            fig = self._px.box(
                data,
                x=graph_def.color_field,
                y=graph_def.field,
                title=graph_def.title,
                color=graph_def.color_field,
                color_discrete_sequence=self._px.colors.qualitative.Set2,
            )
        else:
            fig = self._px.box(
                data,
                y=graph_def.field,
                title=graph_def.title,
                color_discrete_sequence=[self._px.colors.qualitative.Set2[0]],
            )

        return fig

    def _generate_line(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a line chart."""
        # If we have field_y, use it; otherwise plot field over index
        if graph_def.field_y:
            clean_data = data[
                data[graph_def.field].notna() & data[graph_def.field_y].notna()
            ]
            fig = self._px.line(
                clean_data,
                x=graph_def.field,
                y=graph_def.field_y,
                color=graph_def.color_field,
                title=graph_def.title,
                color_discrete_sequence=self._px.colors.qualitative.Set2,
            )
        else:
            clean_data = data[data[graph_def.field].notna()]
            fig = self._px.line(
                clean_data,
                y=graph_def.field,
                title=graph_def.title,
                color_discrete_sequence=[self._px.colors.qualitative.Set2[0]],
            )

        return fig

    def _generate_radar(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a radar chart.

        For radar charts, we expect field to be a list of fields or
        data should already be in the right format with one column per metric.
        """
        # This is a simplified radar chart - typically used for comparing multiple metrics
        # We'll create a radar chart showing the mean of each numeric column

        # Get all numeric columns if field is "*", otherwise use specified field
        if graph_def.field == "*":
            numeric_cols = data.select_dtypes(include=["number"]).columns.tolist()
        else:
            # Field should be comma-separated list of fields
            numeric_cols = [f.strip() for f in graph_def.field.split(",")]

        # Calculate mean for each field
        means = data[numeric_cols].mean()

        fig = self._go.Figure()
        fig.add_trace(
            self._go.Scatterpolar(
                r=means.values,
                theta=means.index,
                fill="toself",
                name="Average",
            )
        )

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, means.max() * 1.1])),
            title=graph_def.title,
        )

        return fig

    def _generate_heatmap(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a heatmap."""
        # Create pivot table for heatmap
        pivot = data.pivot_table(
            values=graph_def.field if graph_def.aggregation else None,
            index=graph_def.field,
            columns=graph_def.field_y,
            aggfunc=graph_def.aggregation or "count",
        )

        fig = self._px.imshow(
            pivot,
            title=graph_def.title,
            color_continuous_scale=graph_def.color_scheme,
            aspect="auto",
        )

        return fig

    def _generate_violin(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a violin plot."""
        # Similar to box plot but shows distribution
        if graph_def.color_field:
            fig = self._px.violin(
                data,
                x=graph_def.color_field,
                y=graph_def.field,
                title=graph_def.title,
                color=graph_def.color_field,
                box=True,
                color_discrete_sequence=self._px.colors.qualitative.Set2,
            )
        else:
            fig = self._px.violin(
                data,
                y=graph_def.field,
                title=graph_def.title,
                box=True,
                color_discrete_sequence=[self._px.colors.qualitative.Set2[0]],
            )

        return fig

    def _generate_polar(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a polar chart (for circular data like time of day)."""
        # For time of day, we'll create a polar bar chart
        value_counts = data[graph_def.field].value_counts().sort_index()

        fig = self._go.Figure()
        fig.add_trace(
            self._go.Barpolar(
                r=value_counts.values,
                theta=value_counts.index,
                marker_color=self._px.colors.qualitative.Set2[0],
            )
        )

        fig.update_layout(
            title=graph_def.title,
            polar=dict(angularaxis=dict(direction="clockwise")),
        )

        return fig

    def _add_kde_overlay(self, fig: "go.Figure", series: pd.Series):
        """Add KDE (kernel density estimate) overlay to histogram.

        Args:
            fig: Plotly figure to add KDE to
            series: Data series to calculate KDE from
        """
        try:
            # pylint: disable=import-outside-toplevel
            from scipy import stats
            import numpy as np

            # Calculate KDE
            kde = stats.gaussian_kde(series.dropna())
            x_range = np.linspace(series.min(), series.max(), 100)
            kde_values = kde(x_range)

            # Scale KDE to match histogram
            hist_max = max([trace.y.max() for trace in fig.data if hasattr(trace, "y")])
            kde_scaled = kde_values * hist_max / kde_values.max()

            # Add KDE trace
            fig.add_trace(
                self._go.Scatter(
                    x=x_range,
                    y=kde_scaled,
                    mode="lines",
                    name="KDE",
                    line=dict(color="red", width=2),
                )
            )
        except Exception as e:
            logger.warning(f"Could not add KDE overlay: {e}")
