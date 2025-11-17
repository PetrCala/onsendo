"""Core graph generation logic.

This module generates individual Plotly figures from GraphDefinition objects.
"""

import warnings
from typing import Optional

import numpy as np
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
        """Generate a histogram with optimal binning.

        Uses Freedman-Diaconis rule for continuous data and integer-centered
        bins for discrete data. For numeric data with many unique values,
        uses continuous bins with minimum width to ensure visibility.
        """
        # Remove null values
        clean_data = data[data[graph_def.field].notna()]

        if clean_data.empty:
            # Return empty figure if no data
            fig = self._go.Figure()
            fig.update_layout(title=graph_def.title)
            return fig

        series = clean_data[graph_def.field]
        min_val = series.min()
        max_val = series.max()
        value_range = max_val - min_val
        unique_count = series.nunique()

        # Check if data is integer-like (all values are integers)
        is_integer_data = all(
            isinstance(x, (int, pd.Int64Dtype))
            or (isinstance(x, float) and x.is_integer())
            for x in series.dropna()
        )

        # Determine if we should use continuous bins
        # Use continuous bins if:
        # 1. Not integer data, OR
        # 2. Integer data but has many unique values (more than 30) OR
        # 3. Integer data with large range relative to unique count (sparse distribution)
        use_continuous_bins = (
            not is_integer_data
            or unique_count > 30
            or (value_range > 0 and unique_count / value_range < 0.5)
        )

        if use_continuous_bins:
            # Use continuous bins with optimal width calculation
            bin_width = self._calculate_optimal_bin_width(series)

            logger.debug(
                f"Histogram binning: field={graph_def.field}, "
                f"min={min_val:.2f}, max={max_val:.2f}, "
                f"range={value_range:.2f}, bin_width={bin_width:.2f}"
            )

            # Create histogram with explicit bin width and range
            # Pass xbins directly to px.histogram to ensure proper binning
            fig = self._px.histogram(
                clean_data,
                x=graph_def.field,
                color=graph_def.color_field,
                title=graph_def.title,
                color_discrete_sequence=self._px.colors.qualitative.Set2,
                nbins=None,  # Don't use nbins with custom xbins
                histfunc="count",
            )

            # Set continuous bins with calculated width
            # Use update_traces to set xbins for all traces
            # Combine with hovertemplate update to ensure both are applied
            fig.update_traces(
                xbins=dict(
                    start=min_val,
                    end=max_val,
                    size=bin_width,
                ),
                hovertemplate="<b>Range: %{x}</b><br>"
                + "Count: %{y}<br>"
                + "<extra></extra>",
            )

            # Explicitly set x-axis range to match data
            # This is critical to prevent Plotly from auto-calculating wrong ranges
            fig.update_xaxes(range=[min_val, max_val])

            # Also set in layout to ensure it's applied
            fig.update_layout(xaxis=dict(range=[min_val, max_val]))

            # Add KDE overlay if requested
            if graph_def.show_kde:
                self._add_kde_overlay(fig, series)
        else:
            # Small integer range (like ratings 1-10), use explicit bins centered on integers
            # Create bins centered on integer values
            # e.g., for ratings 1-10: bins at 0.5, 1.5, 2.5, ..., 10.5
            fig = self._px.histogram(
                clean_data,
                x=graph_def.field,
                color=graph_def.color_field,
                title=graph_def.title,
                color_discrete_sequence=self._px.colors.qualitative.Set2,
                nbins=None,  # Don't use nbins with custom range
            )

            # Update x-axis to use our bin edges
            fig.update_traces(
                xbins=dict(start=min_val - 0.5, end=max_val + 0.5, size=1.0)
            )

            # Set x-axis ticks to integer values and range
            fig.update_xaxes(
                tickmode="linear",
                tick0=min_val,
                dtick=1,
                range=[min_val - 0.5, max_val + 0.5],
            )

            # Also set in layout
            fig.update_layout(xaxis=dict(range=[min_val - 0.5, max_val + 0.5]))

        # Update hover template for clearer information (if not already set)
        # For histograms, Plotly provides bin info in hover
        # Only update if we didn't already set it in the continuous bins branch
        if not use_continuous_bins:
            fig.update_traces(
                hovertemplate="<b>Range: %{x}</b><br>"
                + "Count: %{y}<br>"
                + "<extra></extra>"
            )

        fig.update_layout(showlegend=True if graph_def.color_field else False)
        return fig

    def _calculate_optimal_bin_width(self, series: pd.Series) -> float:
        """Calculate optimal bin width for continuous histograms.

        Uses Freedman-Diaconis rule with smart constraints to ensure bins are
        visible but not too wide. For data with many unique values (like entry fees),
        ensures minimum bin width to prevent 1-2px bins.

        Args:
            series: Data series to calculate bin width for

        Returns:
            Optimal bin width (balanced for visibility and detail)
        """
        n = len(series)
        if n < 2:
            return 1.0

        data_range = series.max() - series.min()
        if data_range == 0:
            return 1.0

        unique_count = series.nunique()

        # Calculate IQR (interquartile range)
        q75, q25 = np.percentile(series, [75, 25])
        iqr = q75 - q25

        # If IQR is 0 (all values in middle 50% are the same), fall back to std
        if iqr == 0:
            # Use standard deviation as fallback
            std_dev = series.std()
            if std_dev > 0:
                # Use Scott's rule: bin_width = 3.5 * std / n^(1/3)
                bin_width = 3.5 * std_dev / (n ** (1 / 3))
            else:
                # All values are the same, use Sturges' formula
                num_bins = max(5, min(50, int(np.ceil(np.log2(n) + 1))))
                bin_width = data_range / num_bins if num_bins > 0 else 1.0
        else:
            # Freedman-Diaconis rule
            bin_width = 2 * iqr / (n ** (1 / 3))

        # Determine if this is a sparse distribution (like entry fees with many unique values)
        # vs dense distribution (like temperatures with fewer unique values)
        density_ratio = unique_count / data_range if data_range > 0 else 1.0
        is_sparse_distribution = unique_count > 30 and density_ratio < 0.5

        # For sparse distributions with many unique values (like entry fees),
        # ensure minimum bin width to prevent bins from being too narrow (1-2px).
        # For dense distributions (like temperatures), use the calculated width as-is.
        if is_sparse_distribution:
            # Sparse distribution - ensure minimum visibility
            min_bin_width = max(data_range * 0.01, 1.0)
            bin_width = max(bin_width, min_bin_width)

        # Determine target number of bins based on data characteristics
        # Sparse distributions (entry fees) can have fewer bins to prevent 1-2px bins
        # Dense distributions (temperatures, travel times) need more bins for detail
        # For dense distributions, ensure we have at least 5 bins
        # For sparse distributions, allow fewer bins but at least 3
        min_required_bins = 3 if is_sparse_distribution else 5

        if is_sparse_distribution:
            # Sparse: aim for 5-20 bins (fewer bins, wider to prevent 1-2px)
            target_min_bins = 5
            target_max_bins = 20
        else:
            # Dense: aim for 10-30 bins (more bins, narrower for detail)
            target_min_bins = 10
            target_max_bins = 30

        # Adjust bin_width to achieve target bin count
        num_bins = data_range / bin_width if bin_width > 0 else 1
        if num_bins > target_max_bins:
            bin_width = data_range / target_max_bins
        elif num_bins < target_min_bins:
            bin_width = data_range / target_min_bins

        # Safety check: ensure bin_width doesn't exceed data_range
        # This prevents creating 1-bin histograms
        bin_width = min(bin_width, data_range / min_required_bins)

        # Round to reasonable precision based on data scale
        # Use smart rounding that preserves reasonable bin counts
        def round_bin_width(bw: float, dr: float) -> float:
            """Round bin width intelligently based on data range."""
            if dr > 1000:
                return max(100, round(bw / 100) * 100)
            elif dr > 100:
                return max(10, round(bw / 50) * 50)
            elif dr > 10:
                # For ranges 10-100, use finer granularity
                if bw < 1:
                    return 1.0
                elif bw < 2:
                    return round(bw * 2) / 2  # 0.5, 1.0, 1.5, 2.0
                elif bw < 5:
                    return round(bw)  # Nearest integer: 2, 3, 4, 5
                else:
                    return round(bw / 5) * 5  # Nearest 5: 5, 10, 15, ...
            elif dr > 1:
                return max(0.5, round(bw * 2) / 2)  # Nearest 0.5
            else:
                return max(0.1, round(bw * 10) / 10)  # Nearest 0.1

        bin_width = round_bin_width(bin_width, data_range)

        # Verify final bin count and adjust if needed
        # This is critical to prevent 1-bin histograms
        final_num_bins = data_range / bin_width if bin_width > 0 else 1

        if final_num_bins < min_required_bins:
            # Recalculate with target bin count
            target_bins = min_required_bins
            bin_width = data_range / target_bins
            bin_width = round_bin_width(bin_width, data_range)
            # Final safety: ensure we don't create too few bins
            final_num_bins = data_range / bin_width if bin_width > 0 else 1
            if final_num_bins < min_required_bins:
                # Last resort: use exact division
                bin_width = data_range / min_required_bins

        # Ensure bin_width is valid: positive, not larger than range
        bin_width = max(0.1, min(bin_width, data_range))

        logger.debug(
            f"Calculated bin width {bin_width:.2f} for {len(series)} data points "
            f"(range: {series.min():.2f}-{series.max():.2f}, "
            f"IQR: {iqr:.2f}, unique: {unique_count}, density: {density_ratio:.3f})"
        )

        return float(bin_width)

    def _calculate_optimal_bins(self, series: pd.Series) -> int:
        """Calculate optimal number of bins using Freedman-Diaconis rule.

        The Freedman-Diaconis rule is robust to outliers and works well for
        various data distributions.

        Formula:
            bin_width = 2 * IQR / n^(1/3)
            num_bins = (max - min) / bin_width

        Args:
            series: Data series to calculate bins for

        Returns:
            Optimal number of bins (between 5 and 50)
        """
        n = len(series)
        if n < 2:
            return 1

        # Calculate IQR (interquartile range)
        q75, q25 = np.percentile(series, [75, 25])
        iqr = q75 - q25

        # If IQR is 0 (all values in middle 50% are the same), fall back to std
        if iqr == 0:
            # Use Sturges' formula as fallback
            num_bins = int(np.ceil(np.log2(n) + 1))
        else:
            # Freedman-Diaconis rule
            bin_width = 2 * iqr / (n ** (1 / 3))

            # Calculate number of bins
            data_range = series.max() - series.min()
            if bin_width > 0:
                num_bins = int(np.ceil(data_range / bin_width))
            else:
                num_bins = int(np.ceil(np.log2(n) + 1))

        # Constrain to reasonable range (5-50 bins)
        num_bins = max(5, min(50, num_bins))

        logger.debug(
            f"Calculated {num_bins} bins for {len(series)} data points "
            f"(range: {series.min():.2f}-{series.max():.2f})"
        )

        return num_bins

    def _generate_pie(
        self, graph_def: GraphDefinition, data: pd.DataFrame
    ) -> "go.Figure":
        """Generate a pie chart."""
        # Count occurrences of each value
        value_counts = data[graph_def.field].value_counts()

        # Apply limit if specified
        if graph_def.limit:
            value_counts = value_counts.head(graph_def.limit)

        # Calculate percentages to determine which labels to show
        total = value_counts.sum()
        percentages = (value_counts.values / total) * 100

        # Create custom text: only show for slices >= 5%
        custom_text = []
        for i, pct in enumerate(percentages):
            if pct >= 5:
                # Show label and percentage for larger slices
                custom_text.append(f"{value_counts.index[i]}<br>{pct:.1f}%")
            else:
                # Hide text for small slices
                custom_text.append("")

        fig = self._px.pie(
            values=value_counts.values,
            names=value_counts.index,
            title=graph_def.title,
            color_discrete_sequence=self._px.colors.qualitative.Set3,
            hole=0.3,  # Donut style makes charts more prominent
        )

        # Update traces with custom text and enhanced hover
        fig.update_traces(
            text=custom_text,
            textposition="inside",
            textinfo="text",  # Use our custom text
            textfont_size=14,
            # Custom hover template with clear formatting (shows for all slices)
            hovertemplate="<b>%{label}</b><br>"
            + "Count: %{value}<br>"
            + "Percentage: %{percent}<br>"
            + "<extra></extra>",  # Hide trace name in hover
            marker={"line": {"color": "white", "width": 2}},
        )
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

        # Update hover template for clearer information
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>" + "Count: %{y}<br>" + "<extra></extra>"
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

        # Update hover template for clearer information
        x_label = graph_def.field.replace("_", " ").title()
        y_label = graph_def.field_y.replace("_", " ").title()
        fig.update_traces(
            hovertemplate=f"<b>{x_label}:</b> %{{x}}<br>"
            + f"<b>{y_label}:</b> %{{y}}<br>"
            + "<extra></extra>"
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

        # Update hover template for clearer box plot statistics
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>"
            + "Max: %{y}<br>"
            + "Upper Quartile (Q3): %{q3}<br>"
            + "Median: %{median}<br>"
            + "Lower Quartile (Q1): %{q1}<br>"
            + "Min: %{lowerfence}<br>"
            + "<extra></extra>"
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
