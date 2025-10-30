"""
Main analysis engine for orchestrating onsen analysis.
"""

import pandas as pd
import numpy as np
from typing import Optional, Any
import time
from datetime import datetime
from pathlib import Path
import json

from loguru import logger

from src.types.analysis import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisType,
    DataCategory,
    MetricType,
    VisualizationType,
    ModelType,
    AnalysisScenario,
    ANALYSIS_SCENARIOS,
    VisualizationConfig,
    ModelConfig,
)
from src.analysis.data_pipeline import DataPipeline
from src.analysis.metrics import MetricsCalculator
from src.analysis.visualizations import VisualizationEngine
from src.analysis.models import ModelEngine

# Import new professional analysis modules
from src.analysis.feature_engineering import FeatureEngineer
from src.analysis.econometrics import EconometricAnalyzer
from src.analysis.insight_discovery import InsightDiscovery
from src.analysis.report_generator import ReportGenerator
from src.analysis.interactive_maps import InteractiveMapGenerator
from src.analysis.model_search import ModelSearchEngine


class AnalysisEngine:
    """
    Main engine for orchestrating comprehensive onsen analysis.
    """

    def __init__(self, session, output_dir: Optional[str] = None):
        self.session = session
        self.base_output_dir = (
            Path(output_dir) if output_dir else Path("output/analysis")
        )
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

        # Analysis-specific output directory will be set when run_analysis is called
        self.output_dir = None
        self.analysis_timestamp = None

        # Initialize components (will be updated with analysis-specific paths)
        self.data_pipeline = DataPipeline(session)
        self.metrics_calculator = MetricsCalculator()
        self.visualization_engine = None  # Will be initialized per analysis
        self.model_engine = None  # Will be initialized per analysis

        # Cache for analysis results
        self._analysis_cache: dict[str, AnalysisResult] = {}

    def _setup_analysis_directory(self, request: AnalysisRequest) -> None:
        """Set up the analysis-specific output directory."""
        # Create timestamp for this analysis
        self.analysis_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create analysis name from request
        analysis_name = f"{request.analysis_type.value}_{self.analysis_timestamp}"

        # Create analysis-specific output directory
        self.output_dir = self.base_output_dir / analysis_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components with analysis-specific paths
        self.visualization_engine = VisualizationEngine(
            self.output_dir / "visualizations",
            db_session=self.session
        )
        self.model_engine = ModelEngine(self.output_dir / "models")

        logger.info(f"Analysis output directory: {self.output_dir}")

    def run_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Run a comprehensive analysis based on the request.

        Args:
            request: Analysis request configuration

        Returns:
            Analysis result with data, metrics, visualizations, and insights
        """
        start_time = time.time()

        try:
            logger.info(f"Starting analysis: {request.analysis_type.value}")

            # Set up analysis-specific output directory
            self._setup_analysis_directory(request)

            # Get data
            data = self._get_analysis_data(request)

            if data.empty:
                raise ValueError("No data available for analysis")

            # Calculate metrics
            metrics = self._calculate_metrics(data, request)

            # Create visualizations
            visualizations = self._create_visualizations(data, request)

            # Create models if requested
            models = None
            if request.models:
                models = self._create_models(data, request)

            # Generate insights
            insights = self._generate_insights(data, metrics, models, request)

            # Perform statistical tests if requested
            statistical_tests = None
            if request.include_statistical_tests:
                statistical_tests = self._perform_statistical_tests(data, request)

            # Create result
            result = AnalysisResult(
                request=request,
                data=data,
                metrics=metrics,
                visualizations=visualizations,
                models=models,
                insights=insights,
                statistical_tests=statistical_tests,
                execution_time=time.time() - start_time,
                metadata={
                    "analysis_date": datetime.now().isoformat(),
                    "data_shape": data.shape,
                    "data_columns": list(data.columns),
                    "missing_values": data.isnull().sum().to_dict(),
                    "output_directory": str(self.output_dir),
                },
            )

            # Cache the result
            cache_key = self._generate_cache_key(request)
            self._analysis_cache[cache_key] = result

            # Save results
            self._save_analysis_results(result)

            logger.info(f"Analysis completed in {result.execution_time:.2f} seconds")
            return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Return error result
            return AnalysisResult(
                request=request,
                data=pd.DataFrame(),
                metrics={},
                visualizations={},
                errors=[str(e)],
                execution_time=time.time() - start_time,
            )

    def run_scenario_analysis(
        self, scenario: AnalysisScenario, custom_config: Optional[dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Run a predefined analysis scenario.

        Args:
            scenario: Predefined analysis scenario
            custom_config: Optional custom configuration overrides

        Returns:
            Analysis result
        """
        if scenario not in ANALYSIS_SCENARIOS:
            raise ValueError(f"Unknown analysis scenario: {scenario}")

        scenario_config = ANALYSIS_SCENARIOS[scenario]

        # Create analysis request from scenario
        request = AnalysisRequest(
            analysis_type=scenario_config.analysis_types[0],  # Use first analysis type
            data_categories=scenario_config.data_categories,
            metrics=scenario_config.metrics,
            visualizations=scenario_config.visualizations,
            models=scenario_config.models,
            filters=scenario_config.filters,
            grouping=scenario_config.grouping,
            custom_metrics=scenario_config.custom_metrics,
        )

        # Apply custom configuration overrides
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(request, key):
                    setattr(request, key, value)

        return self.run_analysis(request)

    def _get_analysis_data(self, request: AnalysisRequest) -> pd.DataFrame:
        """Get data for analysis based on the request."""
        # Check cache first
        cache_key = self._generate_cache_key(request)
        cached_data = self.data_pipeline.get_cached_data(cache_key)

        if cached_data is not None:
            logger.info("Using cached data")
            return cached_data

        # Get fresh data
        data = self.data_pipeline.get_data_for_categories(
            categories=request.data_categories,
            filters=request.filters,
            time_range=request.time_range,
            spatial_bounds=request.spatial_bounds,
        )

        # Cache the data
        self.data_pipeline.cache_data(cache_key, data)

        return data

    def _calculate_metrics(
        self, data: pd.DataFrame, request: AnalysisRequest
    ) -> dict[str, Any]:
        """Calculate metrics based on the request."""
        # Use simplified metrics calculator - summary stats and correlations only
        metrics = {}

        # Get summary statistics
        metrics["summary"] = self.metrics_calculator.calculate_summary_statistics(data)

        # Get numeric summary for quick stats
        metrics["numeric"] = self.metrics_calculator.get_numeric_summary(data)

        # Get correlation matrix if requested
        if MetricType.CUSTOM in request.metrics or any(
            m in [MetricType.CUSTOM] for m in request.metrics
        ):
            corr_matrix = self.metrics_calculator.calculate_correlation_matrix(data)
            if not corr_matrix.empty:
                metrics["correlations"] = corr_matrix.to_dict()

        return metrics

    def _create_visualizations(
        self, data: pd.DataFrame, request: AnalysisRequest
    ) -> dict[str, Any]:
        """Create visualizations based on the request."""
        visualizations = {}

        for viz_type in request.visualizations:
            try:
                # Create visualization configuration
                config = self._create_visualization_config(viz_type, data, request)

                # Create visualization
                viz = self.visualization_engine.create_visualization(data, config)

                if viz is not None:
                    visualizations[viz_type.value] = {
                        "visualization": viz,
                        "config": config,
                        "type": viz_type.value,
                    }

                    # Save visualization
                    if config.save_path:
                        self.visualization_engine.save_visualization(
                            viz, config.save_path
                        )

            except Exception as e:
                logger.warning(f"Failed to create visualization {viz_type.value}: {e}")
                continue

        return visualizations

    def _create_visualization_config(
        self, viz_type: VisualizationType, data: pd.DataFrame, request: AnalysisRequest
    ) -> VisualizationConfig:
        """Create visualization configuration based on type and data."""
        # Generate save path
        save_path = (
            self.output_dir
            / "visualizations"
            / f"{viz_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        if viz_type in [
            VisualizationType.POINT_MAP,
            VisualizationType.HEAT_MAP,
            VisualizationType.CLUSTER_MAP,
            VisualizationType.CHOROPLETH,
        ]:
            save_path = save_path.with_suffix(".html")
        else:
            save_path = save_path.with_suffix(".png")

        # Create basic configuration
        config = VisualizationConfig(
            type=viz_type,
            title=f"{viz_type.value.replace('_', ' ').title()} - {request.analysis_type.value.title()}",
            save_path=str(save_path),
            interactive=True,
        )

        # Set specific configurations based on visualization type
        if viz_type == VisualizationType.CORRELATION_MATRIX:
            config.title = "Correlation Matrix"
        elif viz_type == VisualizationType.TREND:
            config.title = "Trend Analysis"
        elif viz_type == VisualizationType.SEASONAL:
            config.title = "Seasonal Patterns"
        elif viz_type == VisualizationType.CLUSTER:
            config.title = "Cluster Analysis"
        elif viz_type in [VisualizationType.POINT_MAP, VisualizationType.HEAT_MAP]:
            config.title = "Geographic Distribution"

        return config

    def _create_models(
        self, data: pd.DataFrame, request: AnalysisRequest
    ) -> Optional[dict[str, Any]]:
        """
        Create models based on the request.

        Note: Only clustering and dimensionality reduction are supported.
        For regression analysis, use run_econometric_analysis() instead.
        """
        if not request.models:
            return None

        models = {}

        for model_type in request.models:
            try:
                # Only support clustering and dimensionality reduction
                if model_type not in [
                    ModelType.KMEANS,
                    ModelType.DBSCAN,
                    ModelType.PCA,
                    ModelType.TSNE,
                ]:
                    logger.warning(
                        f"Model type {model_type.value} not supported in basic analysis. "
                        f"Use run_econometric_analysis() for regression models."
                    )
                    continue

                # Create model configuration
                config = self._create_model_config(model_type, data, request)

                # Create and train model
                if model_type in [ModelType.KMEANS, ModelType.DBSCAN]:
                    result = self.model_engine.create_clustering_model(data, config)
                elif model_type in [ModelType.PCA, ModelType.TSNE]:
                    result = self.model_engine.create_dimensionality_reduction_model(
                        data, config
                    )

                models[model_type.value] = result

            except Exception as e:
                logger.warning(f"Failed to create model {model_type.value}: {e}")
                continue

        return models if models else None

    def _create_model_config(
        self, model_type: ModelType, data: pd.DataFrame, request: AnalysisRequest
    ) -> ModelConfig:
        """Create model configuration for clustering/dimensionality reduction."""
        # Select numeric columns for features
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_cols:
            raise ValueError("No numeric columns available for modeling")

        # Clustering and dimensionality reduction don't need target columns
        if model_type in [ModelType.KMEANS, ModelType.DBSCAN]:
            feature_cols = numeric_cols[: min(5, len(numeric_cols))]
        elif model_type in [ModelType.PCA, ModelType.TSNE]:
            feature_cols = numeric_cols[: min(10, len(numeric_cols))]
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        return ModelConfig(
            type=model_type,
            target_column="dummy",  # Not used for clustering/dim reduction
            feature_columns=feature_cols,
            hyperparameters=(
                request.custom_metrics.get("hyperparameters", {})
                if request.custom_metrics
                else None
            ),
        )

    def _generate_insights(
        self,
        data: pd.DataFrame,
        metrics: dict[str, Any],
        models: Optional[dict[str, Any]],
        request: AnalysisRequest,
    ) -> list[str]:
        """
        Generate basic insights from the analysis results.

        Note: For comprehensive econometric insights, use InsightDiscovery
        from src.analysis.insight_discovery
        """
        insights = []

        # Data quality insights
        total_rows = len(data)
        if total_rows > 0 and len(data.columns) > 0:
            missing_data = data.isnull().sum().sum()
            missing_percentage = (missing_data / (total_rows * len(data.columns))) * 100

            if missing_percentage > 20:
                insights.append(
                    f"Data quality concern: {missing_percentage:.1f}% of values are missing."
                )
            elif missing_percentage > 5:
                insights.append(
                    f"Moderate data quality: {missing_percentage:.1f}% of values are missing."
                )
            elif missing_percentage == 0:
                insights.append("Good data quality: No missing values.")
            else:
                insights.append(
                    f"Good data quality: Only {missing_percentage:.1f}% of values are missing."
                )

        # Basic numeric summary insights
        if "numeric" in metrics and metrics["numeric"]:
            if "personal_rating" in metrics["numeric"]:
                rating_stats = metrics["numeric"]["personal_rating"]
                avg_rating = rating_stats.get("mean", 0)
                if avg_rating > 8:
                    insights.append(
                        f"High satisfaction: Average rating is {avg_rating:.1f}/10"
                    )
                elif avg_rating > 6:
                    insights.append(
                        f"Moderate satisfaction: Average rating is {avg_rating:.1f}/10"
                    )
                elif avg_rating > 0:
                    insights.append(
                        f"Low satisfaction: Average rating is {avg_rating:.1f}/10"
                    )

        # Spatial coverage
        if request.analysis_type == AnalysisType.SPATIAL:
            if "latitude" in data.columns and "longitude" in data.columns:
                lat_range = data["latitude"].max() - data["latitude"].min()
                lon_range = data["longitude"].max() - data["longitude"].min()
                insights.append(
                    f"Geographic coverage: {lat_range:.2f}° latitude × {lon_range:.2f}° longitude"
                )

        # Temporal coverage
        elif request.analysis_type == AnalysisType.TEMPORAL:
            if "visit_time" in data.columns:
                date_range = data["visit_time"].max() - data["visit_time"].min()
                insights.append(f"Time coverage: {date_range.days} days of data")

        # Clustering insights
        if models:
            for model_name, model_result in models.items():
                if model_result.get("n_clusters"):
                    insights.append(
                        f"Found {model_result['n_clusters']} clusters in the data"
                    )
                if (
                    "metrics" in model_result
                    and "silhouette_score" in model_result["metrics"]
                ):
                    score = model_result["metrics"]["silhouette_score"]
                    quality = (
                        "excellent"
                        if score > 0.7
                        else "good" if score > 0.5 else "moderate"
                    )
                    insights.append(
                        f"Clustering quality: {quality} (silhouette score: {score:.3f})"
                    )

        return insights

    def _perform_statistical_tests(
        self, data: pd.DataFrame, request: AnalysisRequest
    ) -> Optional[dict[str, Any]]:
        """Perform statistical tests based on the analysis type."""
        tests = {}

        try:
            if request.analysis_type == AnalysisType.CORRELATIONAL:
                # Correlation analysis
                numeric_data = data.select_dtypes(include=[np.number])
                if not numeric_data.empty:
                    corr_matrix = numeric_data.corr()
                    tests["correlation_matrix"] = corr_matrix.to_dict()

                    # Find significant correlations
                    significant_correlations = []
                    for i in range(len(corr_matrix.columns)):
                        for j in range(i + 1, len(corr_matrix.columns)):
                            corr_value = corr_matrix.iloc[i, j]
                            if abs(corr_value) > 0.5:
                                significant_correlations.append(
                                    {
                                        "variable1": corr_matrix.columns[i],
                                        "variable2": corr_matrix.columns[j],
                                        "correlation": corr_value,
                                    }
                                )

                    tests["significant_correlations"] = significant_correlations

            elif request.analysis_type == AnalysisType.COMPARATIVE:
                # T-tests for numeric variables across groups
                if request.grouping and len(request.grouping) > 0:
                    group_col = request.grouping[0]
                    if group_col in data.columns:
                        numeric_cols = data.select_dtypes(include=[np.number]).columns
                        t_test_results = {}

                        for col in numeric_cols:
                            if col != group_col:
                                groups = data.groupby(group_col)[col]
                                if len(groups) == 2:  # Only perform t-test for 2 groups
                                    from scipy import stats

                                    group1, group2 = list(groups)
                                    if len(group1) > 1 and len(group2) > 1:
                                        t_stat, p_value = stats.ttest_ind(
                                            group1, group2
                                        )
                                        t_test_results[col] = {
                                            "t_statistic": t_stat,
                                            "p_value": p_value,
                                            "significant": p_value < 0.05,
                                        }

                        tests["t_tests"] = t_test_results

            elif request.analysis_type == AnalysisType.TREND:
                # Trend analysis
                if "visit_time" in data.columns:
                    # Simple linear trend test
                    numeric_cols = data.select_dtypes(include=[np.number]).columns
                    trend_results = {}

                    for col in numeric_cols:
                        if col != "visit_time":
                            # Create time index
                            time_data = data[["visit_time", col]].dropna()
                            if len(time_data) > 10:  # Need sufficient data
                                time_data = time_data.sort_values("visit_time")
                                time_index = np.arange(len(time_data))
                                values = time_data[col].values

                                # Fit linear trend
                                z = np.polyfit(time_index, values, 1)
                                slope = z[0]

                                # Calculate R-squared
                                p = np.poly1d(z)
                                y_pred = p(time_index)
                                r_squared = 1 - (
                                    np.sum((values - y_pred) ** 2)
                                    / np.sum((values - np.mean(values)) ** 2)
                                )

                                trend_results[col] = {
                                    "slope": slope,
                                    "r_squared": r_squared,
                                    "trend_direction": (
                                        "increasing" if slope > 0 else "decreasing"
                                    ),
                                    "trend_strength": (
                                        "strong" if r_squared > 0.5 else "weak"
                                    ),
                                }

                    tests["trend_analysis"] = trend_results

        except Exception as e:
            logger.warning(f"Failed to perform statistical tests: {e}")
            tests["error"] = str(e)

        return tests if tests else None

    def _generate_cache_key(self, request: AnalysisRequest) -> str:
        """Generate a cache key for the analysis request."""
        # Create a hashable representation of the request
        key_parts = [
            request.analysis_type.value,
            ",".join(sorted([cat.value for cat in request.data_categories])),
            ",".join(sorted([metric.value for metric in request.metrics])),
            ",".join(sorted([viz.value for viz in request.visualizations])),
            str(request.filters) if request.filters else "",
            ",".join(request.grouping) if request.grouping else "",
            str(request.time_range) if request.time_range else "",
            str(request.spatial_bounds) if request.spatial_bounds else "",
        ]

        return "_".join(key_parts)

    def _save_analysis_results(self, result: AnalysisResult) -> None:
        """Save analysis results to disk."""
        try:
            # Use analysis-specific output directory
            if not self.output_dir:
                logger.error("Analysis output directory not set")
                return

            # Save data summary
            data_summary = {
                "shape": result.data.shape,
                "columns": list(result.data.columns),
                "missing_values": result.data.isnull().sum().to_dict(),
                "dtypes": {k: str(v) for k, v in result.data.dtypes.to_dict().items()},
            }

            summary_path = self.output_dir / "analysis_summary.json"
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(data_summary, f, indent=2, default=str)

            # Save metrics
            metrics_path = self.output_dir / "metrics.json"
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(result.metrics, f, indent=2, default=str)

            # Save insights
            insights_path = self.output_dir / "insights.txt"
            with open(insights_path, "w", encoding="utf-8") as f:
                f.write("Analysis Insights\n")
                f.write("=" * 50 + "\n\n")
                for i, insight in enumerate(result.insights, 1):
                    f.write(f"{i}. {insight}\n")

            # Save metadata
            metadata_path = self.output_dir / "metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(result.metadata, f, indent=2, default=str)

            logger.info(f"Analysis results saved to {self.output_dir}")

        except Exception as e:
            logger.error(f"Failed to save analysis results: {e}")

    def get_current_analysis_directory(self) -> Optional[Path]:
        """Get the current analysis output directory."""
        return self.output_dir

    def list_analysis_directories(self) -> list[Path]:
        """List all analysis directories."""
        if not self.base_output_dir.exists():
            return []

        analysis_dirs = []
        for item in self.base_output_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                analysis_dirs.append(item)

        # Sort by creation time (newest first)
        analysis_dirs.sort(key=lambda x: x.stat().st_ctime, reverse=True)
        return analysis_dirs

    def get_analysis_summary(self) -> dict[str, Any]:
        """Get a summary of all analyses performed."""
        summary = {
            "total_analyses": len(self._analysis_cache),
            "analyses": [],
            "base_output_directory": str(self.base_output_dir),
            "analysis_directories": [],
            "cache_size": len(self._analysis_cache),
        }

        # Add information about analysis directories
        analysis_dirs = self.list_analysis_directories()
        for analysis_dir in analysis_dirs:
            dir_info = {
                "name": analysis_dir.name,
                "path": str(analysis_dir),
                "created": datetime.fromtimestamp(
                    analysis_dir.stat().st_ctime
                ).isoformat(),
                "size": sum(
                    f.stat().st_size for f in analysis_dir.rglob("*") if f.is_file()
                ),
                "file_count": len(list(analysis_dir.rglob("*"))),
            }
            summary["analysis_directories"].append(dir_info)

        for cache_key, result in self._analysis_cache.items():
            analysis_info = {
                "cache_key": cache_key,
                "analysis_type": result.request.analysis_type.value,
                "data_categories": [
                    cat.value for cat in result.request.data_categories
                ],
                "execution_time": result.execution_time,
                "data_shape": result.data.shape if not result.data.empty else None,
                "insights_count": len(result.insights),
                "visualizations_count": len(result.visualizations),
                "models_count": len(result.models) if result.models else 0,
                "errors": result.errors,
                "warnings": result.warnings,
            }
            summary["analyses"].append(analysis_info)

        return summary

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._analysis_cache.clear()
        self.data_pipeline.clear_cache()
        logger.info("Analysis cache cleared")

    def cleanup_old_analysis_directories(self, keep_recent: int = 5) -> None:
        """Clean up old analysis directories, keeping only the most recent ones."""
        try:
            analysis_dirs = self.list_analysis_directories()

            # Filter out non-analysis directories (like 'models', 'visualizations')
            analysis_dirs = [
                d for d in analysis_dirs if "_" in d.name and d.name.count("_") >= 2
            ]

            if len(analysis_dirs) <= keep_recent:
                logger.info(
                    f"No cleanup needed. Keeping {len(analysis_dirs)} analysis directories."
                )
                return

            # Remove old directories
            to_remove = analysis_dirs[keep_recent:]
            for old_dir in to_remove:
                import shutil

                shutil.rmtree(old_dir)
                logger.info(f"Removed old analysis directory: {old_dir.name}")

            logger.info(
                f"Cleanup completed. Kept {keep_recent} recent analysis directories."
            )

        except Exception as e:
            logger.error(f"Failed to cleanup old analysis directories: {e}")

    def cleanup_shared_directories(self) -> None:
        """Clean up old shared directories that are no longer needed."""
        try:
            shared_dirs = ["models", "visualizations"]

            for dir_name in shared_dirs:
                shared_dir = self.base_output_dir / dir_name
                if shared_dir.exists():
                    import shutil

                    shutil.rmtree(shared_dir)
                    logger.info(f"Removed old shared directory: {dir_name}")

            logger.info("Shared directories cleanup completed.")

        except Exception as e:
            logger.error(f"Failed to cleanup shared directories: {e}")

    def export_results(
        self, result: AnalysisResult, format: str = "json"
    ) -> Optional[str]:
        """Export analysis results in the specified format."""
        try:
            # Use analysis-specific output directory
            if not self.output_dir:
                logger.error("Analysis output directory not set")
                return None

            if format == "json":
                export_path = self.output_dir / "export.json"
                export_data = {
                    "request": {
                        "analysis_type": result.request.analysis_type.value,
                        "data_categories": [
                            cat.value for cat in result.request.data_categories
                        ],
                        "metrics": [metric.value for metric in result.request.metrics],
                        "visualizations": [
                            viz.value for viz in result.request.visualizations
                        ],
                    },
                    "metadata": result.metadata,
                    "insights": result.insights,
                    "metrics_summary": result.metrics,
                    "execution_time": result.execution_time,
                }

                with open(export_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, default=str)

                return str(export_path)

            elif format == "csv":
                # Export data to CSV
                export_path = self.output_dir / "data_export.csv"
                result.data.to_csv(export_path, index=False)
                return str(export_path)

            else:
                logger.warning(f"Unsupported export format: {format}")
                return None

        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return None

    def generate_overview_summary(self, result: AnalysisResult) -> str:
        """
        Generate a console-friendly overview summary from analysis results.

        Args:
            result: Analysis result to summarize

        Returns:
            Formatted summary string for console output
        """
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("ONSEN DATA OVERVIEW")
        lines.append("=" * 70)

        # Dataset dimensions
        if not result.data.empty:
            lines.append(
                f"\n📊 Dataset: {result.data.shape[0]} rows × {result.data.shape[1]} columns"
            )

            # Data quality
            if "summary" in result.metrics and result.metrics["summary"]:
                summary = result.metrics["summary"]
                total_cells = result.data.shape[0] * result.data.shape[1]
                if total_cells > 0:
                    missing_pct = (
                        sum(summary.get("missing_values", {}).values()) / total_cells
                    ) * 100
                    lines.append(f"   Data completeness: {100 - missing_pct:.1f}%")

        # Categorical summaries
        if (
            "summary" in result.metrics
            and "categorical_summary" in result.metrics["summary"]
        ):
            cat_summary = result.metrics["summary"]["categorical_summary"]

            # Regions
            if "region" in cat_summary:
                region_data = cat_summary["region"]
                lines.append(
                    f"\n🗺️  Regions: {region_data['unique_count']} unique regions"
                )
                top_regions = list(region_data["top_values"].items())[:3]
                for region, count in top_regions:
                    lines.append(f"   • {region}: {count} onsens")

            # Business forms
            if "business_form" in cat_summary:
                business_data = cat_summary["business_form"]
                lines.append(
                    f"\n🏢 Business Types: {business_data['unique_count']} categories"
                )
                top_types = list(business_data["top_values"].items())[:3]
                for btype, count in top_types:
                    lines.append(f"   • {btype}: {count} onsens")

            # Spring quality
            if "spring_quality" in cat_summary:
                spring_data = cat_summary["spring_quality"]
                lines.append(
                    f"\n💧 Spring Quality: {spring_data['unique_count']} types"
                )
                top_springs = list(spring_data["top_values"].items())[:3]
                for stype, count in top_springs:
                    lines.append(f"   • {stype}: {count} onsens")

            # Admission fees
            if "admission_fee" in cat_summary:
                fee_data = cat_summary["admission_fee"]
                top_fees = list(fee_data["top_values"].items())[:5]
                lines.append("\n💰 Most Common Admission Fees:")
                for fee, count in top_fees:
                    lines.append(f"   • {fee}: {count} onsens")

        # Numeric summaries
        if "numeric" in result.metrics and result.metrics["numeric"]:
            numeric = result.metrics["numeric"]

            # Geographic coverage
            if "latitude" in numeric and "longitude" in numeric:
                lat_range = numeric["latitude"]["max"] - numeric["latitude"]["min"]
                lon_range = numeric["longitude"]["max"] - numeric["longitude"]["min"]
                lines.append("\n🌍 Geographic Coverage:")
                lines.append(
                    f"   Latitude range: {lat_range:.4f}° ({numeric['latitude']['min']:.4f} to {numeric['latitude']['max']:.4f})"
                )
                lines.append(
                    f"   Longitude range: {lon_range:.4f}° ({numeric['longitude']['min']:.4f} to {numeric['longitude']['max']:.4f})"
                )

        # Visualizations
        if result.visualizations:
            lines.append(
                f"\n📈 Visualizations: {len(result.visualizations)} charts generated"
            )
            for viz_type, viz_data in result.visualizations.items():
                if "config" in viz_data and viz_data["config"].save_path:
                    path = viz_data["config"].save_path
                    lines.append(f"   • {viz_type}: {path}")

        # Execution stats
        if result.execution_time:
            lines.append(
                f"\n⏱️  Analysis completed in {result.execution_time:.2f} seconds"
            )

        # Output directory
        if result.metadata and "output_directory" in result.metadata:
            output_dir = result.metadata["output_directory"]
            lines.append(f"\n📁 Output directory: {output_dir}")
            lines.append("   • metrics.json - Detailed statistics")
            lines.append("   • visualizations/ - Charts and maps")
            lines.append("   • insights.txt - Analysis insights")

        lines.append("\n" + "=" * 70 + "\n")

        return "\n".join(lines)

    def run_econometric_analysis(
        self,
        dependent_var: str = "personal_rating",
        data_categories: Optional[list[DataCategory]] = None,
        max_models: int = 20,
        analysis_name: str = "Econometric Analysis",
    ) -> dict[str, Any]:
        """
        Run comprehensive econometric analysis with automated insights.

        This is the main entry point for professional econometric analysis.
        Integrates feature engineering, model search, diagnostics, insights,
        and report generation.

        Args:
            dependent_var: Dependent variable (default: 'personal_rating')
            data_categories: Data categories to include (default: all relevant)
            max_models: Maximum number of model specifications to test
            analysis_name: Name for the analysis

        Returns:
            Dict with paths to generated outputs and key results
        """
        start_time = time.time()
        logger.info(f"Starting comprehensive econometric analysis: {analysis_name}")

        # Set up output directory
        self.analysis_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_dir_name = f"econometric_{self.analysis_timestamp}"
        self.output_dir = self.base_output_dir / analysis_dir_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Get data
            if data_categories is None:
                data_categories = [
                    DataCategory.VISIT_RATINGS,
                    DataCategory.VISIT_EXPERIENCE,
                    DataCategory.VISIT_PHYSICAL,
                    DataCategory.VISIT_LOGISTICS,
                    DataCategory.ONSEN_FEATURES,
                    DataCategory.WEATHER,
                    DataCategory.TEMPORAL,
                    DataCategory.HEART_RATE,
                ]

            logger.info("Fetching data...")
            data = self.data_pipeline.get_data_for_categories(data_categories)

            if data.empty:
                raise ValueError("No data available for analysis")

            logger.info(
                f"Data loaded: {data.shape[0]} observations, {data.shape[1]} variables"
            )

            # Step 2: Feature Engineering
            logger.info("Applying feature engineering...")
            engineer = FeatureEngineer()
            enhanced_data = engineer.engineer_features(
                data=data,
                include_transformations=True,
                include_interactions=True,
                include_polynomials=True,
                include_temporal=True,
                include_aggregations=True,
                include_heart_rate=True,
            )

            logger.info(
                f"Feature engineering complete: {len(enhanced_data.columns)} total features"
            )

            # Save enhanced data
            enhanced_data.to_csv(
                self.output_dir / "transformed_features.csv", index=False
            )

            # Step 3: Model Search
            logger.info("Running automated model search...")
            analyzer = EconometricAnalyzer()
            search_engine = ModelSearchEngine(analyzer)

            regression_results = search_engine.search_models(
                data=enhanced_data,
                dependent_var=dependent_var,
                max_models=max_models,
                include_polynomials=True,
                include_interactions=True,
            )

            logger.info(f"Estimated {len(regression_results)} models")

            # Get best models
            best_models = search_engine.get_best_models(top_n=5)

            # Step 4: Insight Discovery
            logger.info("Discovering insights...")
            discovery = InsightDiscovery()
            insights = discovery.discover_insights(
                regression_results=best_models,
                data=enhanced_data,
                dependent_var=dependent_var,
            )

            logger.info(f"Discovered {len(insights)} insights")

            # Step 5: Create Interactive Maps
            logger.info("Creating interactive maps...")
            map_generator = InteractiveMapGenerator(self.output_dir / "maps")

            map_files = {}
            if (
                "latitude" in enhanced_data.columns
                and "longitude" in enhanced_data.columns
            ):
                # Main overview map
                overview_map = map_generator.create_comprehensive_onsen_map(
                    data=enhanced_data,
                    db_session=self.session,
                    map_name="onsen_overview.html",
                )
                if overview_map:
                    map_files["overview"] = str(overview_map)

                # Rating heatmap
                rating_map = map_generator.create_rating_heatmap(
                    data=enhanced_data,
                    map_name="rating_heatmap.html",
                )
                if rating_map:
                    map_files["rating_heatmap"] = str(rating_map)

            # Step 6: Generate Report
            logger.info("Generating HTML report...")
            report_generator = ReportGenerator(self.output_dir)

            # Prepare data summary
            data_summary = {
                "n_observations": len(enhanced_data),
                "n_variables": len(enhanced_data.columns),
                "date_range": (
                    f"{enhanced_data['visit_time'].min()} to {enhanced_data['visit_time'].max()}"
                    if "visit_time" in enhanced_data.columns
                    else "N/A"
                ),
            }

            # Generate HTML report
            report_path = report_generator.generate_html_report(
                regression_results=best_models,
                insights=insights,
                visualizations={},  # Maps are saved separately
                data_summary=data_summary,
                analysis_name=analysis_name,
            )

            # Generate markdown summary
            md_summary = report_generator.generate_markdown_summary(
                regression_results=best_models,
                insights=insights,
            )

            # Step 7: Save model comparison
            model_comparison = search_engine.compare_specifications()
            model_comparison.to_csv(
                self.output_dir / "model_comparison.csv", index=False
            )

            # Save regression tables
            for i, result in enumerate(best_models, 1):
                # Save coefficients
                result.coefficients.to_csv(
                    self.output_dir / f"model_{i}_coefficients.csv", index=False
                )

            # Calculate execution time
            execution_time = time.time() - start_time

            # Prepare return value
            output = {
                "status": "success",
                "execution_time": execution_time,
                "output_directory": str(self.output_dir),
                "report_path": str(report_path),
                "markdown_summary": str(md_summary),
                "n_models_estimated": len(regression_results),
                "n_insights_discovered": len(insights),
                "best_model": {
                    "name": best_models[0].model_name if best_models else None,
                    "adj_r2": best_models[0].adj_r_squared if best_models else None,
                    "quality": best_models[0].overall_quality if best_models else None,
                },
                "map_files": map_files,
                "feature_summary": engineer.get_feature_summary(),
            }

            logger.info(f"Econometric analysis complete in {execution_time:.2f}s")
            logger.info(f"Report saved to: {report_path}")
            logger.info(f"Open report in browser: file://{report_path}")

            return output

        except Exception as e:
            logger.error(f"Econometric analysis failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "output_directory": str(self.output_dir) if self.output_dir else None,
            }
