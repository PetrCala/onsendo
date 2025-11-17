"""Base classes and types for the graphing system.

This module provides foundational classes for generating graphs and dashboards
in a scalable, maintainable way.
"""

from dataclasses import dataclass
from dataclasses import field as dataclass_field
from enum import Enum
from typing import Optional


class GraphType(Enum):
    """Types of graphs that can be generated."""

    HISTOGRAM = "histogram"
    PIE = "pie"
    BAR = "bar"
    SCATTER = "scatter"
    BOX = "box"
    LINE = "line"
    RADAR = "radar"
    HEATMAP = "heatmap"
    VIOLIN = "violin"
    POLAR = "polar"


class DataSource(Enum):
    """Data sources for graphs."""

    VISIT = "visit"
    WEIGHT = "weight"
    EXERCISE = "exercise"
    ACTIVITY = "activity"
    ONSEN = "onsen"


class GraphCategory(Enum):
    """Categories for organizing graphs."""

    FINANCIAL = "financial"
    CATEGORICAL = "categorical"
    PHYSICAL = "physical"
    TIME = "time"
    RATINGS = "ratings"
    MOOD = "mood"
    SPATIAL = "spatial"


@dataclass
class GraphDefinition:  # pylint: disable=too-many-instance-attributes
    """Definition of a graph to be generated.

    This dataclass declaratively specifies what graph to generate and how.
    It's designed to be simple to create and easy to extend.
    Many attributes are needed for flexibility across different graph types.

    Attributes:
        title: Graph title
        graph_type: Type of graph to generate
        data_source: Source of data (visit, weight, exercise, etc.)
        category: Category for organization
        field: Primary field to graph (e.g., "entry_fee_yen")
        field_y: Secondary field for 2D graphs (optional)
        color_field: Field to use for color grouping (optional)
        bins: Number of bins for histograms (default: 20)
        color_scheme: Plotly color scheme (default: "viridis")
        show_kde: Show KDE overlay for histograms (default: False)
        filters: Data filters to apply (optional)
        aggregation: Aggregation function for grouped data (optional)
        sort_by: Field to sort by (optional)
        limit: Limit number of items displayed (optional)
        notes: Additional notes or description
    """

    title: str
    graph_type: GraphType
    data_source: DataSource
    category: GraphCategory
    field: str
    field_y: Optional[str] = None
    color_field: Optional[str] = None
    bins: int = 20
    color_scheme: str = "viridis"
    show_kde: bool = False
    filters: dict = dataclass_field(default_factory=dict)
    aggregation: Optional[str] = None  # "mean", "sum", "count", etc.
    sort_by: Optional[str] = None
    limit: Optional[int] = None
    notes: str = ""

    def __post_init__(self):
        """Validate the graph definition."""
        # Convert string enums to enum instances if needed
        if isinstance(self.graph_type, str):
            self.graph_type = GraphType(self.graph_type)
        if isinstance(self.data_source, str):
            self.data_source = DataSource(self.data_source)
        if isinstance(self.category, str):
            self.category = GraphCategory(self.category)

        # Validate graph type requirements
        if self.graph_type in {GraphType.SCATTER, GraphType.HEATMAP}:
            if not self.field_y:
                raise ValueError(
                    f"{self.graph_type.value} requires field_y to be specified"
                )


@dataclass
class DashboardConfig:
    """Configuration for a dashboard containing multiple graphs.

    Attributes:
        title: Dashboard title
        data_source: Primary data source
        graph_definitions: List of graphs to include
        columns: Number of columns in grid layout (default: 3)
        show_summary: Show summary statistics header (default: True)
        output_filename: Output filename (default: auto-generated)
    """

    title: str
    data_source: DataSource
    graph_definitions: list[GraphDefinition]
    columns: int = 3
    show_summary: bool = True
    output_filename: Optional[str] = None

    def __post_init__(self):
        """Validate dashboard configuration."""
        if isinstance(self.data_source, str):
            self.data_source = DataSource(self.data_source)

        if not self.graph_definitions:
            raise ValueError("Dashboard must have at least one graph definition")

        # Validate all graphs use compatible data source
        for graph_def in self.graph_definitions:
            if graph_def.data_source != self.data_source:
                raise ValueError(
                    f"Graph '{graph_def.title}' uses data source "
                    f"'{graph_def.data_source.value}' but dashboard expects "
                    f"'{self.data_source.value}'"
                )
