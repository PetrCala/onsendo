"""
Basic functionality tests for the analysis system.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock

from src.types.analysis import (
    AnalysisType,
    DataCategory,
    MetricType,
    VisualizationType,
    AnalysisRequest,
    AnalysisResult,
)
from src.analysis.metrics import MetricsCalculator
from src.analysis.visualizations import VisualizationEngine
from src.analysis.models import ModelEngine


class TestMetricsCalculator:
    """Test the metrics calculator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = MetricsCalculator()

        # Create sample data
        self.sample_data = pd.DataFrame(
            {
                "rating": [8, 7, 9, 6, 8, 7, 9, 8],
                "price": [500, 600, 800, 400, 700, 550, 900, 650],
                "category": ["A", "B", "A", "C", "B", "A", "A", "B"],
            }
        )

    def test_calculate_basic_metrics(self):
        """Test basic metric calculations."""
        metrics = self.calculator.calculate_metrics(
            self.sample_data, [MetricType.MEAN, MetricType.MEDIAN, MetricType.STD]
        )

        assert "overall" in metrics
        overall = metrics["overall"]

        # Check that mean was calculated
        assert "mean" in overall
        assert "rating" in overall["mean"]
        assert overall["mean"]["rating"] == 7.75

        # Check that median was calculated
        assert "median" in overall
        assert "price" in overall["median"]
        assert overall["median"]["price"] == 625.0

        # Check that std was calculated
        assert "std" in overall
        assert "rating" in overall["std"]
        assert overall["std"]["rating"] == pytest.approx(1.035, rel=1e-2)

    def test_calculate_grouped_metrics(self):
        """Test grouped metric calculations."""
        metrics = self.calculator.calculate_metrics(
            self.sample_data, [MetricType.MEAN, MetricType.COUNT], grouping=["category"]
        )

        # Should have groups for each category
        assert "A" in metrics
        assert "B" in metrics
        assert "C" in metrics

        # Check group A metrics
        group_a = metrics["A"]
        assert "mean" in group_a
        assert "count" in group_a
        assert group_a["count"]["rating"] == 5  # 5 items in category A

    def test_correlation_matrix(self):
        """Test correlation matrix calculation."""
        corr_matrix = self.calculator.calculate_correlation_matrix(self.sample_data)

        assert not corr_matrix.empty
        assert "rating" in corr_matrix.columns
        assert "price" in corr_matrix.columns
        assert corr_matrix.shape == (3, 3)  # 3 numeric columns

    def test_summary_statistics(self):
        """Test comprehensive summary statistics."""
        summary = self.calculator.calculate_summary_statistics(self.sample_data)

        assert "shape" in summary
        assert "columns" in summary
        assert "missing_values" in summary
        assert "dtypes" in summary

        assert summary["shape"] == (8, 3)
        assert len(summary["columns"]) == 3


class TestVisualizationEngine:
    """Test the visualization engine functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = VisualizationEngine()

        # Create sample data
        self.sample_data = pd.DataFrame(
            {
                "category": ["A", "B", "C", "A", "B"],
                "value": [10, 20, 15, 12, 18],
                "rating": [8, 7, 9, 6, 8],
            }
        )

    def test_create_bar_chart(self):
        """Test bar chart creation."""
        from src.types.analysis import VisualizationConfig

        config = VisualizationConfig(
            type=VisualizationType.BAR,
            title="Test Bar Chart",
            x_column="category",
            y_column="value",
        )

        viz = self.engine.create_visualization(self.sample_data, config)
        assert viz is not None

    def test_create_histogram(self):
        """Test histogram creation."""
        from src.types.analysis import VisualizationConfig

        config = VisualizationConfig(
            type=VisualizationType.HISTOGRAM, title="Test Histogram", x_column="rating"
        )

        viz = self.engine.create_visualization(self.sample_data, config)
        assert viz is not None

    def test_create_correlation_matrix(self):
        """Test correlation matrix creation."""
        from src.types.analysis import VisualizationConfig

        config = VisualizationConfig(
            type=VisualizationType.CORRELATION_MATRIX, title="Test Correlation Matrix"
        )

        viz = self.engine.create_visualization(self.sample_data, config)
        assert viz is not None


class TestModelEngine:
    """Test the model engine functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = ModelEngine()

        # Create sample data
        np.random.seed(42)
        self.sample_data = pd.DataFrame(
            {
                "feature1": np.random.randn(100),
                "feature2": np.random.randn(100),
                "target": np.random.randn(100) + 0.5 * np.random.randn(100),
            }
        )

    def test_create_linear_regression(self):
        """Test linear regression model creation."""
        from src.types.analysis import ModelConfig, ModelType

        config = ModelConfig(
            type=ModelType.LINEAR_REGRESSION,
            target_column="target",
            feature_columns=["feature1", "feature2"],
        )

        result = self.engine.create_model(self.sample_data, config)

        assert result is not None
        assert "model" in result
        assert "metrics" in result
        assert "feature_names" in result
        assert result["model_type"] == "linear_regression"

    def test_create_clustering_model(self):
        """Test clustering model creation."""
        from src.types.analysis import ModelConfig, ModelType

        config = ModelConfig(
            type=ModelType.KMEANS,
            target_column="dummy",
            feature_columns=["feature1", "feature2"],
        )

        result = self.engine.create_clustering_model(self.sample_data, config)

        assert result is not None
        assert "model" in result
        assert "cluster_labels" in result
        assert "n_clusters" in result
        assert result["model_type"] == "kmeans"


class TestAnalysisTypes:
    """Test analysis type definitions."""

    def test_analysis_types(self):
        """Test that all analysis types are properly defined."""
        assert AnalysisType.DESCRIPTIVE == "descriptive"
        assert AnalysisType.EXPLORATORY == "exploratory"
        assert AnalysisType.PREDICTIVE == "predictive"
        assert AnalysisType.CORRELATIONAL == "correlational"
        assert AnalysisType.SPATIAL == "spatial"
        assert AnalysisType.TEMPORAL == "temporal"

    def test_data_categories(self):
        """Test that all data categories are properly defined."""
        assert DataCategory.ONSEN_BASIC == "onsen_basic"
        assert DataCategory.VISIT_BASIC == "visit_basic"
        assert DataCategory.VISIT_RATINGS == "visit_ratings"
        assert DataCategory.SPATIAL == "spatial"
        assert DataCategory.TEMPORAL == "temporal"

    def test_metric_types(self):
        """Test that all metric types are properly defined."""
        assert MetricType.MEAN == "mean"
        assert MetricType.MEDIAN == "median"
        assert MetricType.STD == "std"
        assert MetricType.COUNT == "count"
        assert MetricType.CUSTOM == "custom"

    def test_visualization_types(self):
        """Test that all visualization types are properly defined."""
        assert VisualizationType.BAR == "bar"
        assert VisualizationType.LINE == "line"
        assert VisualizationType.SCATTER == "scatter"
        assert VisualizationType.HISTOGRAM == "histogram"
        assert VisualizationType.CORRELATION_MATRIX == "correlation_matrix"


class TestAnalysisRequest:
    """Test analysis request creation and validation."""

    def test_create_basic_request(self):
        """Test creating a basic analysis request."""
        request = AnalysisRequest(
            analysis_type=AnalysisType.DESCRIPTIVE,
            data_categories=[DataCategory.ONSEN_BASIC, DataCategory.VISIT_BASIC],
            metrics=[MetricType.MEAN, MetricType.COUNT],
            visualizations=[VisualizationType.BAR, VisualizationType.HISTOGRAM],
        )

        assert request.analysis_type == AnalysisType.DESCRIPTIVE
        assert len(request.data_categories) == 2
        assert len(request.metrics) == 2
        assert len(request.visualizations) == 2
        assert request.include_statistical_tests is True
        assert request.confidence_level == 0.95

    def test_create_advanced_request(self):
        """Test creating an advanced analysis request with models."""
        request = AnalysisRequest(
            analysis_type=AnalysisType.CORRELATIONAL,
            data_categories=[DataCategory.VISIT_RATINGS],
            metrics=[MetricType.MEAN, MetricType.STD],
            visualizations=[VisualizationType.CORRELATION_MATRIX],
            models=["linear_regression"],
            grouping=["region"],
            include_raw_data=True,
        )

        assert request.analysis_type == AnalysisType.CORRELATIONAL
        assert request.models is not None
        assert len(request.models) == 1
        assert request.grouping is not None
        assert request.include_raw_data is True


if __name__ == "__main__":
    pytest.main([__file__])
