"""
Analysis types and enums for the onsen analysis system.
"""

from enum import StrEnum
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, date
import pandas as pd


class AnalysisType(StrEnum):
    """Types of analysis that can be performed."""

    DESCRIPTIVE = "descriptive"
    EXPLORATORY = "exploratory"
    PREDICTIVE = "predictive"
    CORRELATIONAL = "correlational"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    COMPARATIVE = "comparative"
    TREND = "trend"
    CLUSTER = "cluster"
    REGRESSION = "regression"
    CLASSIFICATION = "classification"


class VisualizationType(StrEnum):
    """Types of visualizations that can be generated."""

    # Basic charts
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    PIE = "pie"
    HEATMAP = "heatmap"

    # Advanced charts
    CORRELATION_MATRIX = "correlation_matrix"
    DISTRIBUTION = "distribution"
    TREND = "trend"
    SEASONAL = "seasonal"
    CLUSTER = "cluster"

    # Maps
    POINT_MAP = "point_map"
    HEAT_MAP = "heat_map"
    CHOROPLETH = "choropleth"
    CLUSTER_MAP = "cluster_map"

    # Interactive
    INTERACTIVE_CHART = "interactive_chart"
    DASHBOARD = "dashboard"


class MetricType(StrEnum):
    """Types of metrics that can be calculated."""

    # Central tendency
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"

    # Dispersion
    STD = "std"
    VARIANCE = "variance"
    RANGE = "range"
    IQR = "iqr"

    # Distribution
    SKEWNESS = "skewness"
    KURTOSIS = "kurtosis"

    # Counts
    COUNT = "count"
    UNIQUE_COUNT = "unique_count"
    NULL_COUNT = "null_count"

    # Percentiles
    PERCENTILE_25 = "percentile_25"
    PERCENTILE_75 = "percentile_75"
    PERCENTILE_90 = "percentile_90"
    PERCENTILE_95 = "percentile_95"

    # Custom
    CUSTOM = "custom"
    TREND = "trend"


class ModelType(StrEnum):
    """Types of statistical and machine learning models."""

    # Linear models
    LINEAR_REGRESSION = "linear_regression"
    LOGISTIC_REGRESSION = "logistic_regression"
    RIDGE_REGRESSION = "ridge_regression"
    LASSO_REGRESSION = "lasso_regression"

    # Tree-based models
    DECISION_TREE = "decision_tree"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"

    # Clustering
    KMEANS = "kmeans"
    DBSCAN = "dbscan"
    HIERARCHICAL = "hierarchical"

    # Dimensionality reduction
    PCA = "pca"
    TSNE = "tsne"
    UMAP = "umap"


class DataCategory(StrEnum):
    """Categories of data for analysis."""

    ONSEN_BASIC = "onsen_basic"  # Basic onsen information
    ONSEN_FEATURES = "onsen_features"  # Onsen amenities and features
    VISIT_BASIC = "visit_basic"  # Basic visit information
    VISIT_RATINGS = "visit_ratings"  # All rating fields
    VISIT_EXPERIENCE = "visit_experience"  # Experience-related fields
    VISIT_LOGISTICS = "visit_logistics"  # Travel and timing
    VISIT_PHYSICAL = "visit_physical"  # Physical aspects (temperature, etc.)
    HEART_RATE = "heart_rate"  # Heart rate data
    SPATIAL = "spatial"  # Location and distance data
    TEMPORAL = "temporal"  # Time-based data
    WEATHER = "weather"  # Weather-related data
    EXERCISE = "exercise"  # Exercise-related data


class ReportFormat(StrEnum):
    """Formats for analysis reports."""

    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    JUPYTER = "jupyter"
    INTERACTIVE = "interactive"


@dataclass
class AnalysisRequest:
    """Request for an analysis to be performed.

    This class contains many attributes to provide comprehensive
    configuration options for analysis requests.
    """
    # pylint: disable=too-many-instance-attributes

    analysis_type: AnalysisType
    data_categories: list[DataCategory]
    metrics: list[MetricType]
    visualizations: list[VisualizationType]
    models: Optional[list[ModelType]] = None
    filters: Optional[dict[str, Any]] = None
    grouping: Optional[list[str]] = None
    time_range: Optional[tuple[datetime, datetime]] = None
    spatial_bounds: Optional[tuple[float, float, float, float]] = (
        None  # min_lat, max_lat, min_lon, max_lon
    )
    custom_metrics: Optional[dict[str, str]] = None  # name: expression
    output_format: ReportFormat = ReportFormat.HTML
    include_raw_data: bool = False
    include_statistical_tests: bool = True
    confidence_level: float = 0.95


@dataclass
class AnalysisResult:
    """Result of an analysis operation.

    This class contains many attributes to provide comprehensive
    analysis results and metadata.
    """
    # pylint: disable=too-many-instance-attributes

    request: AnalysisRequest
    data: pd.DataFrame
    metrics: dict[str, dict[str, float]]
    visualizations: dict[str, Any]
    models: Optional[dict[str, Any]] = None
    insights: list[str] = field(default_factory=list)
    statistical_tests: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class VisualizationConfig:
    """Configuration for a visualization."""

    type: VisualizationType
    title: str
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    size_column: Optional[str] = None
    facet_column: Optional[str] = None
    custom_config: Optional[dict[str, Any]] = None
    interactive: bool = True
    save_path: Optional[str] = None


@dataclass
class ModelConfig:
    """Configuration for a statistical or machine learning model."""

    type: ModelType
    target_column: str
    feature_columns: list[str]
    hyperparameters: Optional[dict[str, Any]] = None
    validation_split: float = 0.2
    cross_validation_folds: int = 5
    random_state: Optional[int] = 42
    custom_config: Optional[dict[str, Any]] = None


@dataclass
class ReportConfig:
    """Configuration for report generation.

    This class contains many attributes to provide comprehensive
    report configuration options.
    """
    # pylint: disable=too-many-instance-attributes

    title: str
    subtitle: Optional[str] = None
    author: Optional[str] = None
    date: Optional[date] = None
    include_toc: bool = True
    include_executive_summary: bool = True
    include_methodology: bool = True
    include_conclusions: bool = True
    include_recommendations: bool = True
    custom_sections: Optional[list[str]] = None
    styling: Optional[dict[str, Any]] = None
    output_path: Optional[str] = None


class AnalysisScenario(StrEnum):
    """Predefined analysis scenarios."""

    # Basic scenarios
    OVERVIEW = "overview"  # General overview of all data
    QUALITY_ANALYSIS = "quality_analysis"  # Focus on ratings and quality
    PRICING_ANALYSIS = "pricing_analysis"  # Focus on pricing and value
    SPATIAL_ANALYSIS = "spatial_analysis"  # Geographic distribution and patterns
    TEMPORAL_ANALYSIS = "temporal_analysis"  # Time-based patterns and trends

    # Advanced scenarios
    EXPERIENCE_OPTIMIZATION = "experience_optimization"  # What makes a great experience
    SEASONAL_PATTERNS = "seasonal_patterns"  # Seasonal variations
    TRAVEL_ANALYSIS = "travel_analysis"  # Travel patterns and efficiency
    HEALTH_IMPACT = "health_impact"  # Health and wellness impact
    COMPETITIVE_ANALYSIS = "competitive_analysis"  # Compare onsens

    # Custom scenarios
    CUSTOM = "custom"  # User-defined analysis


@dataclass
class AnalysisScenarioConfig:
    """Configuration for a predefined analysis scenario.

    This class contains many attributes to provide comprehensive
    scenario configuration options.
    """
    # pylint: disable=too-many-instance-attributes

    name: AnalysisScenario
    description: str
    analysis_types: list[AnalysisType]
    data_categories: list[DataCategory]
    metrics: list[MetricType]
    visualizations: list[VisualizationType]
    models: Optional[list[ModelType]] = None
    filters: Optional[dict[str, Any]] = None
    grouping: Optional[list[str]] = None
    custom_metrics: Optional[dict[str, str]] = None
    insights_focus: list[str] = field(default_factory=list)
    report_sections: list[str] = field(default_factory=list)


# Predefined analysis scenarios
ANALYSIS_SCENARIOS: dict[AnalysisScenario, AnalysisScenarioConfig] = {
    AnalysisScenario.OVERVIEW: AnalysisScenarioConfig(
        name=AnalysisScenario.OVERVIEW,
        description="Comprehensive overview of all onsen data",
        analysis_types=[AnalysisType.DESCRIPTIVE, AnalysisType.EXPLORATORY],
        data_categories=[
            DataCategory.ONSEN_BASIC,
            DataCategory.VISIT_BASIC,
            DataCategory.VISIT_RATINGS,
            DataCategory.SPATIAL,
            DataCategory.TEMPORAL,
        ],
        metrics=[
            MetricType.MEAN,
            MetricType.MEDIAN,
            MetricType.STD,
            MetricType.COUNT,
            MetricType.UNIQUE_COUNT,
        ],
        visualizations=[
            VisualizationType.BAR,
            VisualizationType.HISTOGRAM,
            VisualizationType.POINT_MAP,
            VisualizationType.HEATMAP,
        ],
        insights_focus=["data_overview", "key_statistics", "data_quality"],
        report_sections=[
            "executive_summary",
            "data_overview",
            "key_findings",
            "recommendations",
        ],
    ),
    AnalysisScenario.QUALITY_ANALYSIS: AnalysisScenarioConfig(
        name=AnalysisScenario.QUALITY_ANALYSIS,
        description="Deep dive into onsen quality metrics and ratings",
        analysis_types=[
            AnalysisType.DESCRIPTIVE,
            AnalysisType.CORRELATIONAL,
            AnalysisType.COMPARATIVE,
        ],
        data_categories=[
            DataCategory.VISIT_RATINGS,
            DataCategory.ONSEN_FEATURES,
            DataCategory.VISIT_EXPERIENCE,
        ],
        metrics=[
            MetricType.MEAN,
            MetricType.MEDIAN,
            MetricType.STD,
            MetricType.PERCENTILE_25,
            MetricType.PERCENTILE_75,
        ],
        visualizations=[
            VisualizationType.BOX,
            VisualizationType.VIOLIN,
            VisualizationType.CORRELATION_MATRIX,
            VisualizationType.HEATMAP,
        ],
        models=[ModelType.LINEAR_REGRESSION],
        insights_focus=["rating_patterns", "quality_factors", "improvement_areas"],
        report_sections=[
            "executive_summary",
            "quality_metrics",
            "correlation_analysis",
            "recommendations",
        ],
    ),
    AnalysisScenario.SPATIAL_ANALYSIS: AnalysisScenarioConfig(
        name=AnalysisScenario.SPATIAL_ANALYSIS,
        description="Geographic analysis of onsen distribution and patterns",
        analysis_types=[
            AnalysisType.SPATIAL,
            AnalysisType.CLUSTER,
            AnalysisType.COMPARATIVE,
        ],
        data_categories=[
            DataCategory.SPATIAL,
            DataCategory.ONSEN_BASIC,
            DataCategory.VISIT_RATINGS,
        ],
        metrics=[MetricType.MEAN, MetricType.COUNT, MetricType.UNIQUE_COUNT],
        visualizations=[
            VisualizationType.POINT_MAP,
            VisualizationType.HEAT_MAP,
            VisualizationType.CLUSTER_MAP,
            VisualizationType.CHOROPLETH,
        ],
        models=[ModelType.KMEANS, ModelType.DBSCAN],
        insights_focus=["geographic_patterns", "clusters", "spatial_correlations"],
        report_sections=[
            "executive_summary",
            "geographic_overview",
            "spatial_patterns",
            "clustering_analysis",
        ],
    ),
    AnalysisScenario.TEMPORAL_ANALYSIS: AnalysisScenarioConfig(
        name=AnalysisScenario.TEMPORAL_ANALYSIS,
        description="Time-based analysis of trends and seasonal patterns",
        analysis_types=[
            AnalysisType.TEMPORAL,
            AnalysisType.TREND,
        ],
        data_categories=[
            DataCategory.TEMPORAL,
            DataCategory.VISIT_BASIC,
            DataCategory.WEATHER,
        ],
        metrics=[MetricType.MEAN, MetricType.COUNT, MetricType.TREND],
        visualizations=[
            VisualizationType.LINE,
            VisualizationType.TREND,
            VisualizationType.SEASONAL,
            VisualizationType.HEATMAP,
        ],
        models=[],
        insights_focus=[
            "temporal_trends",
            "seasonal_patterns",
            "time_based_recommendations",
        ],
        report_sections=[
            "executive_summary",
            "temporal_overview",
            "trend_analysis",
            "seasonal_patterns",
        ],
    ),
}
