"""
Visualization system for onsen analysis.
"""

from typing import Optional, Any
from pathlib import Path

import pandas as pd
import numpy as np
import seaborn as sns
from loguru import logger
from sqlalchemy.orm import Session

from src.types.analysis import VisualizationType, VisualizationConfig
from src.analysis.metrics import MetricsCalculator
from src.lib.map_generator import _add_location_markers


class VisualizationEngine:
    """
    Engine for creating various types of visualizations.
    """

    def __init__(self, save_dir: Optional[str] = None, db_session: Optional[Session] = None):
        self.save_dir = Path(save_dir) if save_dir else Path("output/visualizations")
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_calculator = MetricsCalculator()
        self.db_session = db_session

    def _get_matplotlib(self):
        # pylint: disable=import-outside-toplevel
        # Lazy import for optional heavy dependency - improves startup time
        """Lazy import matplotlib and configure it."""
        import matplotlib.pyplot as _plt
        import seaborn as sns

        # Set style for matplotlib
        _plt.style.use("default")
        sns.set_palette("husl")

        # Configure matplotlib for better quality
        _plt.rcParams["figure.dpi"] = 300
        _plt.rcParams["savefig.dpi"] = 300
        _plt.rcParams["font.size"] = 10

        # Configure seaborn
        sns.set_style("whitegrid")

        return _plt, sns

    def _get_plotly(self):
        # pylint: disable=import-outside-toplevel
        # Lazy import for optional heavy dependency - improves startup time
        """Lazy import plotly."""
        import plotly.express as px
        import plotly.graph_objects as go
        import plotly.subplots as sp

        return px, go, sp

    def _get_folium(self):
        # pylint: disable=import-outside-toplevel
        # Lazy import for optional heavy dependency - improves startup time
        """Lazy import folium."""
        import folium
        from folium.plugins import HeatMap, MarkerCluster

        return folium, HeatMap, MarkerCluster

    def create_visualization(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        # pylint: disable=too-complex,too-many-return-statements
        # Complexity justified: dispatcher for 15+ visualization types
        """
        Create a visualization based on the configuration.

        Args:
            data: DataFrame to visualize
            config: Visualization configuration

        Returns:
            Visualization object (matplotlib figure, plotly figure, or folium map)
        """
        if data.empty:
            logger.warning("Cannot create visualization for empty data")
            return None

        try:
            if config.type == VisualizationType.BAR:
                return self._create_bar_chart(data, config)
            if config.type == VisualizationType.LINE:
                return self._create_line_chart(data, config)
            if config.type == VisualizationType.SCATTER:
                return self._create_scatter_plot(data, config)
            if config.type == VisualizationType.HISTOGRAM:
                return self._create_histogram(data, config)
            if config.type == VisualizationType.BOX:
                return self._create_box_plot(data, config)
            if config.type == VisualizationType.VIOLIN:
                return self._create_violin_plot(data, config)
            if config.type == VisualizationType.PIE:
                return self._create_pie_chart(data, config)
            if config.type == VisualizationType.HEATMAP:
                return self._create_heatmap(data, config)
            if config.type == VisualizationType.CORRELATION_MATRIX:
                return self._create_correlation_matrix(data, config)
            if config.type == VisualizationType.DISTRIBUTION:
                return self._create_distribution_plot(data, config)
            if config.type == VisualizationType.TREND:
                return self._create_trend_plot(data, config)
            if config.type == VisualizationType.SEASONAL:
                return self._create_seasonal_plot(data, config)
            if config.type == VisualizationType.CLUSTER:
                return self._create_cluster_plot(data, config)
            if config.type == VisualizationType.POINT_MAP:
                return self._create_point_map(data, config)
            if config.type == VisualizationType.HEAT_MAP:
                return self._create_heat_map(data, config)
            if config.type == VisualizationType.CHOROPLETH:
                return self._create_choropleth_map(data, config)
            if config.type == VisualizationType.CLUSTER_MAP:
                return self._create_cluster_map(data, config)
            if config.type == VisualizationType.INTERACTIVE_CHART:
                return self._create_interactive_chart(data, config)
            if config.type == VisualizationType.DASHBOARD:
                return self._create_dashboard(data, config)
            raise ValueError(f"Unknown visualization type: {config.type}")

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Broad exception justified: any visualization error should be logged and return None
            logger.error(f"Failed to create visualization {config.type}: {e}")
            return None

    def _create_bar_chart(self, data: pd.DataFrame, config: VisualizationConfig) -> Any:
        """Create a bar chart."""
        if not config.x_column or not config.y_column:
            # Try to infer columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            categorical_cols = data.select_dtypes(
                include=["object", "category"]
            ).columns

            if len(numeric_cols) > 0 and len(categorical_cols) > 0:
                config.x_column = categorical_cols[0]
                config.y_column = numeric_cols[0]
            else:
                raise ValueError("Cannot infer columns for bar chart")

        if data[config.y_column].ndim > 1:
            # If y_column is 2D, take the mean or first column
            if isinstance(data[config.y_column].iloc[0], (list, np.ndarray)):
                data = data.copy()
                data[config.y_column] = data[config.y_column].apply(
                    lambda x: np.mean(x) if isinstance(x, (list, np.ndarray)) else x
                )

        if config.interactive:
            px, _go, _sp = self._get_plotly()
            fig = px.bar(
                data,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                title=config.title,
                labels={
                    config.x_column: config.x_column.replace("_", " ").title(),
                    config.y_column: config.y_column.replace("_", " ").title(),
                },
            )
            fig.update_layout(xaxis_tickangle=-45, showlegend=True)
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(12, 8))

        if config.color_column:
            data.groupby(config.color_column)[config.y_column].mean().plot(
                kind="bar", ax=ax, color=config.color_column
            )
        else:
            data.groupby(config.x_column)[config.y_column].mean().plot(
                kind="bar", ax=ax
            )

        ax.set_title(config.title)
        ax.set_xlabel(config.x_column.replace("_", " ").title())
        ax.set_ylabel(config.y_column.replace("_", " ").title())
        _plt.xticks(rotation=45, ha="right")
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_line_chart(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create a line chart."""
        if not config.x_column or not config.y_column:
            # Try to infer columns
            date_cols = data.select_dtypes(include=["datetime64"]).columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns

            if len(date_cols) > 0 and len(numeric_cols) > 0:
                config.x_column = date_cols[0]
                config.y_column = numeric_cols[0]
            else:
                raise ValueError("Cannot infer columns for line chart")

        if config.interactive:
            px, go, sp = self._get_plotly()
            fig = px.line(
                data,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                title=config.title,
            )
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(12, 8))

        if config.color_column:
            for name, group in data.groupby(config.color_column):
                ax.plot(group[config.x_column], group[config.y_column], label=name)
            ax.legend()
        else:
            ax.plot(data[config.x_column], data[config.y_column])

        ax.set_title(config.title)
        ax.set_xlabel(config.x_column.replace("_", " ").title())
        ax.set_ylabel(config.y_column.replace("_", " ").title())
        _plt.xticks(rotation=45)
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_scatter_plot(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create a scatter plot."""
        if not config.x_column or not config.y_column:
            # Try to infer columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) >= 2:
                config.x_column = numeric_cols[0]
                config.y_column = numeric_cols[1]
            else:
                raise ValueError("Cannot infer columns for scatter plot")

        if config.interactive:
            px, go, sp = self._get_plotly()
            fig = px.scatter(
                data,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                size=config.size_column,
                hover_data=[config.facet_column] if config.facet_column else None,
                title=config.title,
            )
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(10, 8))

        scatter = ax.scatter(
            data[config.x_column],
            data[config.y_column],
            c=data[config.color_column] if config.color_column else None,
            s=data[config.size_column] if config.size_column else 50,
            alpha=0.6,
        )

        ax.set_title(config.title)
        ax.set_xlabel(config.x_column.replace("_", " ").title())
        ax.set_ylabel(config.y_column.replace("_", " ").title())

        if config.color_column:
            _plt.colorbar(scatter, label=config.color_column.replace("_", " ").title())

        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_histogram(self, data: pd.DataFrame, config: VisualizationConfig) -> Any:
        """Create a histogram."""
        if not config.x_column:
            # Try to infer column
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                config.x_column = numeric_cols[0]
            else:
                raise ValueError("Cannot infer column for histogram")

        if data[config.x_column].ndim > 1:
            # If x_column is 2D, take the mean or first column
            if isinstance(data[config.x_column].iloc[0], (list, np.ndarray)):
                data = data.copy()
                data[config.x_column] = data[config.x_column].apply(
                    lambda x: np.mean(x) if isinstance(x, (list, np.ndarray)) else x
                )

        if config.interactive:
            px, go, sp = self._get_plotly()
            fig = px.histogram(
                data,
                x=config.x_column,
                color=config.color_column,
                nbins=30,
                title=config.title,
            )
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(10, 8))

        if config.color_column:
            for name, group in data.groupby(config.color_column):
                ax.hist(group[config.x_column], alpha=0.7, label=name, bins=30)
            ax.legend()
        else:
            ax.hist(data[config.x_column], bins=30, alpha=0.7)

        ax.set_title(config.title)
        ax.set_xlabel(config.x_column.replace("_", " ").title())
        ax.set_ylabel("Frequency")
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_box_plot(self, data: pd.DataFrame, config: VisualizationConfig) -> Any:
        """Create a box plot."""
        if not config.x_column or not config.y_column:
            # Try to infer columns
            categorical_cols = data.select_dtypes(
                include=["object", "category"]
            ).columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns

            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                config.x_column = categorical_cols[0]
                config.y_column = numeric_cols[0]
            else:
                raise ValueError("Cannot infer columns for box plot")

        if config.interactive:
            px, _go, _sp = self._get_plotly()
            fig = px.box(
                data,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                title=config.title,
            )
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(12, 8))

        if config.color_column:
            sns.boxplot(
                data=data,
                x=config.x_column,
                y=config.y_column,
                hue=config.color_column,
                ax=ax,
            )
        else:
            sns.boxplot(data=data, x=config.x_column, y=config.y_column, ax=ax)

        ax.set_title(config.title)
        ax.set_xlabel(config.x_column.replace("_", " ").title())
        ax.set_ylabel(config.y_column.replace("_", " ").title())
        _plt.xticks(rotation=45)
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_violin_plot(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create a violin plot."""
        if not config.x_column or not config.y_column:
            # Try to infer columns
            categorical_cols = data.select_dtypes(
                include=["object", "category"]
            ).columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns

            if len(categorical_cols) > 0 and len(numeric_cols) > 0:
                config.x_column = categorical_cols[0]
                config.y_column = numeric_cols[0]
            else:
                raise ValueError("Cannot infer columns for violin plot")

        if config.interactive:
            px, go, sp = self._get_plotly()
            fig = px.violin(
                data,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                title=config.title,
            )
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(12, 8))

        if config.color_column:
            sns.violinplot(
                data=data,
                x=config.x_column,
                y=config.y_column,
                hue=config.color_column,
                ax=ax,
            )
        else:
            sns.violinplot(data=data, x=config.x_column, y=config.y_column, ax=ax)

        ax.set_title(config.title)
        ax.set_xlabel(config.x_column.replace("_", " ").title())
        ax.set_ylabel(config.y_column.replace("_", " ").title())
        _plt.xticks(rotation=45)
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_pie_chart(self, data: pd.DataFrame, config: VisualizationConfig) -> Any:
        """Create a pie chart."""
        if not config.x_column:
            # Try to infer column
            categorical_cols = data.select_dtypes(
                include=["object", "category"]
            ).columns
            if len(categorical_cols) > 0:
                config.x_column = categorical_cols[0]
            else:
                raise ValueError("Cannot infer column for pie chart")

        if config.interactive:
            px, go, sp = self._get_plotly()
            value_counts = data[config.x_column].value_counts()
            fig = px.pie(
                values=value_counts.values, names=value_counts.index, title=config.title
            )
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(10, 8))

        value_counts = data[config.x_column].value_counts()
        ax.pie(value_counts.values, labels=value_counts.index, autopct="%1.1f%%")
        ax.set_title(config.title)

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_heatmap(self, data: pd.DataFrame, config: VisualizationConfig) -> Any:
        """Create a heatmap."""
        if config.interactive:
            # For interactive heatmap, we need to pivot the data
            if config.x_column and config.y_column and config.color_column:
                pivot_data = data.pivot_table(
                    values=config.color_column,
                    index=config.y_column,
                    columns=config.x_column,
                    aggfunc="mean",
                )
                px, go, sp = self._get_plotly()
                fig = px.imshow(pivot_data, title=config.title, aspect="auto")
                return fig
            else:
                # Use correlation matrix as fallback
                numeric_data = data.select_dtypes(include=[np.number])
                if not numeric_data.empty:
                    corr_matrix = numeric_data.corr()
                    px, go, sp = self._get_plotly()
                    fig = px.imshow(corr_matrix, title=config.title, aspect="auto")
                    return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(12, 10))

        if config.x_column and config.y_column and config.color_column:
            pivot_data = data.pivot_table(
                values=config.color_column,
                index=config.y_column,
                columns=config.x_column,
                aggfunc="mean",
            )
            sns.heatmap(pivot_data, annot=True, cmap="viridis", ax=ax)
        else:
            # Use correlation matrix as fallback
            numeric_data = data.select_dtypes(include=[np.number])
            if not numeric_data.empty:
                corr_matrix = numeric_data.corr()
                sns.heatmap(corr_matrix, annot=True, cmap="viridis", ax=ax)

        ax.set_title(config.title)
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_correlation_matrix(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create a correlation matrix visualization."""
        numeric_data = data.select_dtypes(include=[np.number])

        if numeric_data.empty:
            logger.warning("No numeric columns found for correlation matrix")
            return None

        corr_matrix = self.metrics_calculator.calculate_correlation_matrix(numeric_data)

        if config.interactive:
            px, go, sp = self._get_plotly()
            fig = px.imshow(
                corr_matrix,
                title=config.title,
                aspect="auto",
                color_continuous_scale="RdBu",
            )
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(12, 10))
        sns.heatmap(corr_matrix, annot=True, cmap="RdBu", center=0, square=True, ax=ax)
        ax.set_title(config.title)
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_distribution_plot(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create a distribution plot."""
        if not config.x_column:
            # Try to infer column
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                config.x_column = numeric_cols[0]
            else:
                raise ValueError("Cannot infer column for distribution plot")

        if config.interactive:
            px, go, sp = self._get_plotly()
            fig = px.histogram(
                data,
                x=config.x_column,
                color=config.color_column,
                nbins=30,
                title=config.title,
                marginal="box",
            )
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(12, 8))

        if config.color_column:
            for name, group in data.groupby(config.color_column):
                sns.kdeplot(data=group[config.x_column], label=name, ax=ax)
            ax.legend()
        else:
            sns.kdeplot(data=data[config.x_column], ax=ax)

        ax.set_title(config.title)
        ax.set_xlabel(config.x_column.replace("_", " ").title())
        ax.set_ylabel("Density")
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_trend_plot(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create a trend plot."""
        if not config.x_column or not config.y_column:
            # Try to infer columns
            date_cols = data.select_dtypes(include=["datetime64"]).columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns

            if len(date_cols) > 0 and len(numeric_cols) > 0:
                config.x_column = date_cols[0]
                config.y_column = numeric_cols[0]
            else:
                raise ValueError("Cannot infer columns for trend plot")

        if config.interactive:
            px, go, sp = self._get_plotly()
            fig = px.line(
                data,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                title=config.title,
            )

            # Add trend line
            if config.y_column:
                z = np.polyfit(
                    range(len(data)), data[config.y_column].fillna(method="ffill"), 1
                )
                p = np.poly1d(z)
                fig.add_trace(
                    go.Scatter(
                        x=data[config.x_column],
                        y=p(range(len(data))),
                        mode="lines",
                        name="Trend Line",
                        line=dict(dash="dash", color="red"),
                    )
                )

            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(12, 8))

        if config.color_column:
            for name, group in data.groupby(config.color_column):
                ax.plot(group[config.x_column], group[config.y_column], label=name)
            ax.legend()
        else:
            ax.plot(data[config.x_column], data[config.y_column])

            # Add trend line
            if config.y_column:
                z = np.polyfit(
                    range(len(data)),
                    data[config.y_column].fillna(method="ffill"),
                    1,
                )
                p = np.poly1d(z)
                ax.plot(
                    data[config.x_column],
                    p(range(len(data))),
                    "r--",
                    label="Trend Line",
                )
                ax.legend()

        ax.set_title(config.title)
        ax.set_xlabel(config.x_column.replace("_", " ").title())
        ax.set_ylabel(config.y_column.replace("_", " ").title())
        _plt.xticks(rotation=45)
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_seasonal_plot(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create a seasonal plot."""
        if not config.x_column or not config.y_column:
            # Try to infer columns
            date_cols = data.select_dtypes(include=["datetime64"]).columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns

            if len(date_cols) > 0 and len(numeric_cols) > 0:
                config.x_column = date_cols[0]
                config.y_column = numeric_cols[0]
            else:
                raise ValueError("Cannot infer columns for seasonal plot")

        # Add seasonal columns
        data_copy = data.copy()
        data_copy["month"] = data_copy[config.x_column].dt.month
        data_copy["year"] = data_copy[config.x_column].dt.year

        if config.interactive:
            px, go, sp = self._get_plotly()
            fig = px.line(
                data_copy,
                x="month",
                y=config.y_column,
                color="year",
                title=config.title,
            )
            fig.update_xaxes(
                tickmode="array",
                tickvals=list(range(1, 13)),
                ticktext=[
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ],
            )
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(12, 8))

        for year in data_copy["year"].unique():
            year_data = data_copy[data_copy["year"] == year]
            ax.plot(
                year_data["month"],
                year_data[config.y_column],
                label=str(year),
                marker="o",
            )

        ax.set_title(config.title)
        ax.set_xlabel("Month")
        ax.set_ylabel(config.y_column.replace("_", " ").title())
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(
            [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
        )
        ax.legend()
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_cluster_plot(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create a cluster plot."""
        if not config.x_column or not config.y_column:
            # Try to infer columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) >= 2:
                config.x_column = numeric_cols[0]
                config.y_column = numeric_cols[1]
            else:
                raise ValueError("Cannot infer columns for cluster plot")

        if config.interactive:
            px, go, sp = self._get_plotly()
            fig = px.scatter(
                data,
                x=config.x_column,
                y=config.y_column,
                color=config.color_column,
                title=config.title,
            )
            return fig
        _plt, _sns = self._get_matplotlib()
        fig, ax = _plt.subplots(figsize=(10, 8))

        if config.color_column:
            for name, group in data.groupby(config.color_column):
                ax.scatter(
                    group[config.x_column],
                    group[config.y_column],
                    label=name,
                    alpha=0.7,
                )
            ax.legend()
        else:
            ax.scatter(data[config.x_column], data[config.y_column], alpha=0.7)

        ax.set_title(config.title)
        ax.set_xlabel(config.x_column.replace("_", " ").title())
        ax.set_ylabel(config.y_column.replace("_", " ").title())
        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def _create_point_map(self, data: pd.DataFrame, config: VisualizationConfig) -> Any:
        """Create a point map."""
        if "latitude" not in data.columns or "longitude" not in data.columns:
            logger.error("Point map requires latitude and longitude columns")
            return None

        folium, HeatMap, MarkerCluster = self._get_folium()

        # Filter out rows without coordinates
        map_data = data.dropna(subset=["latitude", "longitude"])

        if map_data.empty:
            logger.warning("No valid coordinates found for point map")
            return None

        # Create base map centered on the data
        center_lat = map_data["latitude"].mean()
        center_lon = map_data["longitude"].mean()

        m = folium.Map(
            location=[center_lat, center_lon], zoom_start=10, tiles="OpenStreetMap"
        )

        # Add location markers if db_session is available
        if self.db_session:
            _add_location_markers(m, self.db_session, reference_location_id=None)

        # Add points
        for _, row in map_data.iterrows():
            popup_text = f"<b>{row.get('name', 'Unknown')}</b><br>"
            if "region" in row:
                popup_text += f"Region: {row['region']}<br>"
            if "address" in row:
                popup_text += f"Address: {row['address']}<br>"

            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=popup_text,
                tooltip=row.get("name", "Unknown"),
            ).add_to(m)

        if config.save_path:
            m.save(config.save_path)

        return m

    def _create_heat_map(self, data: pd.DataFrame, config: VisualizationConfig) -> Any:
        """Create a heat map."""
        if "latitude" not in data.columns or "longitude" not in data.columns:
            logger.error("Heat map requires latitude and longitude columns")
            return None

        folium, HeatMap, MarkerCluster = self._get_folium()

        # Filter out rows without coordinates
        map_data = data.dropna(subset=["latitude", "longitude"])

        if map_data.empty:
            logger.warning("No valid coordinates found for heat map")
            return None

        # Determine the value column for heat intensity
        value_column = config.color_column if config.color_column else "visit_count"
        if value_column not in map_data.columns:
            # Try to find a suitable numeric column
            numeric_cols = map_data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                value_column = numeric_cols[0]
            else:
                logger.warning("No suitable value column found for heat map")
                return None

        # Create base map
        center_lat = map_data["latitude"].mean()
        center_lon = map_data["longitude"].mean()

        m = folium.Map(
            location=[center_lat, center_lon], zoom_start=10, tiles="OpenStreetMap"
        )

        # Add location markers if db_session is available
        if self.db_session:
            _add_location_markers(m, self.db_session, reference_location_id=None)

        # Prepare heat map data
        heat_data = []
        for _, row in map_data.iterrows():
            value = row[value_column]
            if pd.notna(value) and value > 0:
                heat_data.append([row["latitude"], row["longitude"], value])

        if heat_data:
            HeatMap(heat_data, radius=25).add_to(m)

        if config.save_path:
            m.save(config.save_path)

        return m

    def _create_choropleth_map(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create a choropleth map."""
        # This is a simplified version - in production you might want to use actual geographic boundaries
        logger.warning(
            "Choropleth maps require geographic boundary data - creating simplified version"
        )
        return self._create_heat_map(data, config)

    def _create_cluster_map(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create a cluster map."""
        if "latitude" not in data.columns or "longitude" not in data.columns:
            logger.error("Cluster map requires latitude and longitude columns")
            return None

        # Filter out rows without coordinates
        map_data = data.dropna(subset=["latitude", "longitude"])

        if map_data.empty:
            logger.warning("No valid coordinates found for cluster map")
            return None

        # Create base map
        center_lat = map_data["latitude"].mean()
        center_lon = map_data["longitude"].mean()

        # Create marker cluster
        folium, HeatMap, MarkerCluster = self._get_folium()
        m = folium.Map(
            location=[center_lat, center_lon], zoom_start=10, tiles="OpenStreetMap"
        )

        # Add location markers if db_session is available
        if self.db_session:
            _add_location_markers(m, self.db_session, reference_location_id=None)

        marker_cluster = MarkerCluster().add_to(m)

        # Add points to cluster
        for _, row in map_data.iterrows():
            popup_text = f"<b>{row.get('name', 'Unknown')}</b><br>"
            if "region" in row:
                popup_text += f"Region: {row['region']}<br>"
            if "address" in row:
                popup_text += f"Address: {row['address']}<br>"

            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=popup_text,
                tooltip=row.get("name", "Unknown"),
            ).add_to(marker_cluster)

        if config.save_path:
            m.save(config.save_path)

        return m

    def _create_interactive_chart(
        self, data: pd.DataFrame, config: VisualizationConfig
    ) -> Any:
        """Create an interactive chart."""
        # For now, just create a basic interactive scatter plot
        # In production, you might want more sophisticated interactive features
        return self._create_scatter_plot(data, config)

    def _create_dashboard(self, data: pd.DataFrame, config: VisualizationConfig) -> Any:
        """Create a dashboard with multiple visualizations."""
        # This is a simplified dashboard - in production you might want more sophisticated layouts
        if config.interactive:
            px, go, sp = self._get_plotly()
            # Create subplots for interactive dashboard
            fig = sp.make_subplots(
                rows=2,
                cols=2,
                subplot_titles=["Distribution", "Trend", "Correlation", "Summary"],
                specs=[
                    [{"type": "histogram"}, {"type": "scatter"}],
                    [{"type": "heatmap"}, {"type": "bar"}],
                ],
            )

            # Add traces (this is a simplified version)
            if "visit_time" in data.columns and "personal_rating" in data.columns:
                fig.add_trace(
                    go.Histogram(x=data["personal_rating"], name="Rating Distribution"),
                    row=1,
                    col=1,
                )

            fig.update_layout(height=800, title_text=config.title)
            return fig
        _plt, _sns = self._get_matplotlib()
        # Create matplotlib subplots
        fig, axes = _plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(config.title, fontsize=16)

        # This is a simplified version - you'd want to add actual visualizations here
        axes[0, 0].text(
            0.5,
            0.5,
            "Distribution",
            ha="center",
            va="center",
            transform=axes[0, 0].transAxes,
        )
        axes[0, 1].text(
            0.5,
            0.5,
            "Trend",
            ha="center",
            va="center",
            transform=axes[0, 1].transAxes,
        )
        axes[1, 0].text(
            0.5,
            0.5,
            "Correlation",
            ha="center",
            va="center",
            transform=axes[1, 0].transAxes,
        )
        axes[1, 1].text(
            0.5,
            0.5,
            "Summary",
            ha="center",
            va="center",
            transform=axes[1, 1].transAxes,
        )

        _plt.tight_layout()

        if config.save_path:
            _plt.savefig(config.save_path, bbox_inches="tight", dpi=300)

        return fig

    def save_visualization(
        self, visualization: Any, filepath: str, file_format: str = "png"
    ) -> bool:
        """Save a visualization to file."""
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)

            if hasattr(visualization, "savefig"):
                # Matplotlib figure
                visualization.savefig(
                    filepath, bbox_inches="tight", dpi=300, format=file_format
                )
            elif hasattr(visualization, "write_html"):
                # Plotly figure
                visualization.write_html(filepath.with_suffix(".html"))
            elif hasattr(visualization, "save"):
                # Folium map
                visualization.save(filepath.with_suffix(".html"))
            else:
                logger.warning(f"Unknown visualization type: {type(visualization)}")
                return False

            logger.info(f"Visualization saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save visualization: {e}")
            return False

    def create_visualization_grid(
        self,
        data: pd.DataFrame,
        configs: list[VisualizationConfig],
        rows: int = 2,
        cols: int = 2,
    ) -> Any:
        """Create a grid of visualizations."""
        if len(configs) > rows * cols:
            logger.warning(
                f"Too many visualizations ({len(configs)}) for grid size ({rows}x{cols})"
            )
            configs = configs[: rows * cols]

        if len(configs) == 0:
            return None

        # Create subplots
        _plt_local, _sns_local = self._get_matplotlib()
        fig, axes = _plt_local.subplots(rows, cols, figsize=(cols * 6, rows * 5))
        if rows == 1 and cols == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()

        # Create each visualization
        for i, config in enumerate(configs):
            if i < len(axes):
                ax = axes[i]
                viz = self.create_visualization(data, config)

                if hasattr(viz, "savefig"):
                    # For matplotlib figures, we need to handle them differently
                    pass
                else:
                    ax.text(
                        0.5,
                        0.5,
                        f"{config.type.value}",
                        ha="center",
                        va="center",
                        transform=ax.transAxes,
                    )
                    ax.set_title(config.title)

        _plt_local.tight_layout()
        return fig
