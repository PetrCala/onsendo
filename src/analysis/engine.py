"""
Main analysis engine for orchestrating onsen analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
import time
from datetime import datetime
from pathlib import Path
import json

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

logger = logging.getLogger(__name__)


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
        self._analysis_cache: Dict[str, AnalysisResult] = {}

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
            self.output_dir / "visualizations"
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
        self, scenario: AnalysisScenario, custom_config: Optional[Dict[str, Any]] = None
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
    ) -> Dict[str, Dict[str, float]]:
        """Calculate metrics based on the request."""
        return self.metrics_calculator.calculate_metrics(
            data=data,
            metrics=request.metrics,
            grouping=request.grouping,
            custom_metrics=request.custom_metrics,
        )

    def _create_visualizations(
        self, data: pd.DataFrame, request: AnalysisRequest
    ) -> Dict[str, Any]:
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
    ) -> Optional[Dict[str, Any]]:
        """Create models based on the request."""
        if not request.models:
            return None

        models = {}

        for model_type in request.models:
            try:
                # Create model configuration
                config = self._create_model_config(model_type, data, request)

                # Create and train model
                if model_type in [ModelType.KMEANS, ModelType.DBSCAN]:
                    result = self.model_engine.create_clustering_model(data, config)
                elif model_type in [ModelType.PCA, ModelType.TSNE]:
                    result = self.model_engine.create_dimensionality_reduction_model(
                        data, config
                    )
                else:
                    result = self.model_engine.create_model(data, config)

                models[model_type.value] = result

            except Exception as e:
                logger.warning(f"Failed to create model {model_type.value}: {e}")
                continue

        return models if models else None

    def _create_model_config(
        self, model_type: ModelType, data: pd.DataFrame, request: AnalysisRequest
    ) -> ModelConfig:
        """Create model configuration based on type and data."""
        # Select appropriate target and feature columns
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_cols:
            raise ValueError("No numeric columns available for modeling")

        # For now, use simple heuristics for target and feature selection
        # In production, you might want more sophisticated logic

        if model_type in [
            ModelType.LINEAR_REGRESSION,
            ModelType.RIDGE_REGRESSION,
            ModelType.LASSO_REGRESSION,
        ]:
            # Use first numeric column as target, rest as features
            target_col = numeric_cols[0]
            feature_cols = numeric_cols[1 : min(6, len(numeric_cols))]  # Limit features

        elif model_type in [
            ModelType.LOGISTIC_REGRESSION,
            ModelType.DECISION_TREE,
            ModelType.RANDOM_FOREST,
        ]:
            # For classification, try to find a categorical target
            categorical_cols = data.select_dtypes(
                include=["object", "category"]
            ).columns
            if len(categorical_cols) > 0:
                target_col = categorical_cols[0]
            else:
                # Use first numeric column as target
                target_col = numeric_cols[0]
            feature_cols = numeric_cols[: min(5, len(numeric_cols))]

        elif model_type in [ModelType.KMEANS, ModelType.DBSCAN]:
            # For clustering, use numeric columns as features
            target_col = None
            feature_cols = numeric_cols[: min(5, len(numeric_cols))]

        elif model_type in [ModelType.PCA, ModelType.TSNE]:
            # For dimensionality reduction, use numeric columns as features
            target_col = None
            feature_cols = numeric_cols[: min(10, len(numeric_cols))]

        else:
            raise ValueError(f"Unsupported model type: {model_type}")

        return ModelConfig(
            type=model_type,
            target_column=target_col if target_col else "dummy",
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
        metrics: Dict[str, Dict[str, float]],
        models: Optional[Dict[str, Any]],
        request: AnalysisRequest,
    ) -> List[str]:
        """Generate insights from the analysis results."""
        insights = []

        # Data quality insights
        total_rows = len(data)
        missing_data = data.isnull().sum().sum()
        missing_percentage = (missing_data / (total_rows * len(data.columns))) * 100

        if missing_percentage > 20:
            insights.append(
                f"Data quality concern: {missing_percentage:.1f}% of values are missing"
            )
        elif missing_percentage > 5:
            insights.append(
                f"Moderate data quality: {missing_percentage:.1f}% of values are missing"
            )
        else:
            insights.append(
                f"Good data quality: Only {missing_percentage:.1f}% of values are missing"
            )

        # Metric-based insights
        if "overall" in metrics:
            overall_metrics = metrics["overall"]

            # Rating insights
            if (
                "mean" in overall_metrics
                and "personal_rating" in overall_metrics["mean"]
            ):
                avg_rating = overall_metrics["mean"]["personal_rating"]
                if avg_rating > 8:
                    insights.append(
                        f"High satisfaction: Average personal rating is {avg_rating:.1f}/10"
                    )
                elif avg_rating > 6:
                    insights.append(
                        f"Moderate satisfaction: Average personal rating is {avg_rating:.1f}/10"
                    )
                else:
                    insights.append(
                        f"Low satisfaction: Average personal rating is {avg_rating:.1f}/10"
                    )

            # Price insights
            if "mean" in overall_metrics and "entry_fee_yen" in overall_metrics["mean"]:
                avg_price = overall_metrics["mean"]["entry_fee_yen"]
                if avg_price > 1000:
                    insights.append(
                        f"Premium pricing: Average entry fee is ¥{avg_price:.0f}"
                    )
                elif avg_price > 500:
                    insights.append(
                        f"Standard pricing: Average entry fee is ¥{avg_price:.0f}"
                    )
                else:
                    insights.append(
                        f"Budget-friendly: Average entry fee is ¥{avg_price:.0f}"
                    )

        # Model-based insights
        if models:
            for model_name, model_result in models.items():
                if "metrics" in model_result:
                    model_metrics = model_result["metrics"]

                    if "r2" in model_metrics:
                        r2 = model_metrics["r2"]
                        if r2 > 0.7:
                            insights.append(
                                f"Strong model performance: {model_name} explains {r2:.1%} of variance"
                            )
                        elif r2 > 0.5:
                            insights.append(
                                f"Moderate model performance: {model_name} explains {r2:.1%} of variance"
                            )
                        else:
                            insights.append(
                                f"Weak model performance: {model_name} explains {r2:.1%} of variance"
                            )

                    if "accuracy" in model_metrics:
                        accuracy = model_metrics["accuracy"]
                        if accuracy > 0.8:
                            insights.append(
                                f"High classification accuracy: {model_name} achieves {accuracy:.1%} accuracy"
                            )
                        elif accuracy > 0.6:
                            insights.append(
                                f"Moderate classification accuracy: {model_name} achieves {accuracy:.1%} accuracy"
                            )
                        else:
                            insights.append(
                                f"Low classification accuracy: {model_name} achieves {accuracy:.1%} accuracy"
                            )

        # Analysis-specific insights
        if request.analysis_type == AnalysisType.SPATIAL:
            if "latitude" in data.columns and "longitude" in data.columns:
                lat_range = data["latitude"].max() - data["latitude"].min()
                lon_range = data["longitude"].max() - data["longitude"].min()
                insights.append(
                    f"Geographic coverage: {lat_range:.2f}° latitude × {lon_range:.2f}° longitude"
                )

        elif request.analysis_type == AnalysisType.TEMPORAL:
            if "visit_time" in data.columns:
                date_range = data["visit_time"].max() - data["visit_time"].min()
                insights.append(f"Time coverage: {date_range.days} days of data")

        return insights

    def _perform_statistical_tests(
        self, data: pd.DataFrame, request: AnalysisRequest
    ) -> Optional[Dict[str, Any]]:
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
                "dtypes": result.data.dtypes.to_dict(),
            }

            summary_path = self.output_dir / "analysis_summary.json"
            with open(summary_path, "w") as f:
                json.dump(data_summary, f, indent=2, default=str)

            # Save metrics
            metrics_path = self.output_dir / "metrics.json"
            with open(metrics_path, "w") as f:
                json.dump(result.metrics, f, indent=2, default=str)

            # Save insights
            insights_path = self.output_dir / "insights.txt"
            with open(insights_path, "w") as f:
                f.write("Analysis Insights\n")
                f.write("=" * 50 + "\n\n")
                for i, insight in enumerate(result.insights, 1):
                    f.write(f"{i}. {insight}\n")

            # Save metadata
            metadata_path = self.output_dir / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(result.metadata, f, indent=2, default=str)

            logger.info(f"Analysis results saved to {self.output_dir}")

        except Exception as e:
            logger.error(f"Failed to save analysis results: {e}")

    def get_current_analysis_directory(self) -> Optional[Path]:
        """Get the current analysis output directory."""
        return self.output_dir

    def list_analysis_directories(self) -> List[Path]:
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

    def get_analysis_summary(self) -> Dict[str, Any]:
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

                with open(export_path, "w") as f:
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
