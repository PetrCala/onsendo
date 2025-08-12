"""
Metrics calculation system for onsen analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from scipy import stats
from scipy.stats import skew, kurtosis
import logging

from src.types.analysis import MetricType, DataCategory

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Calculator for various statistical metrics used in analysis.
    """

    def __init__(self):
        self._custom_metrics: Dict[str, str] = {}

    def calculate_metrics(
        self,
        data: pd.DataFrame,
        metrics: List[MetricType],
        grouping: Optional[List[str]] = None,
        custom_metrics: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate specified metrics for the given data.

        Args:
            data: DataFrame to analyze
            metrics: List of metrics to calculate
            grouping: Optional columns to group by
            custom_metrics: Optional custom metric definitions

        Returns:
            Dictionary of metrics by group (or overall if no grouping)
        """
        if data.empty:
            return {}

        # Handle custom metrics
        if custom_metrics:
            self._custom_metrics.update(custom_metrics)

        if grouping:
            return self._calculate_grouped_metrics(data, metrics, grouping)
        else:
            return self._calculate_overall_metrics(data, metrics)

    def _calculate_overall_metrics(
        self, data: pd.DataFrame, metrics: List[MetricType]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate metrics for the entire dataset."""
        result = {}

        for metric in metrics:
            try:
                if metric == MetricType.MEAN:
                    result["mean"] = self._calculate_mean(data)
                elif metric == MetricType.MEDIAN:
                    result["median"] = self._calculate_median(data)
                elif metric == MetricType.MODE:
                    result["mode"] = self._calculate_mode(data)
                elif metric == MetricType.STD:
                    result["std"] = self._calculate_std(data)
                elif metric == MetricType.VARIANCE:
                    result["variance"] = self._calculate_variance(data)
                elif metric == MetricType.RANGE:
                    result["range"] = self._calculate_range(data)
                elif metric == MetricType.IQR:
                    result["iqr"] = self._calculate_iqr(data)
                elif metric == MetricType.SKEWNESS:
                    result["skewness"] = self._calculate_skewness(data)
                elif metric == MetricType.KURTOSIS:
                    result["kurtosis"] = self._calculate_kurtosis(data)
                elif metric == MetricType.COUNT:
                    result["count"] = self._calculate_count(data)
                elif metric == MetricType.UNIQUE_COUNT:
                    result["unique_count"] = self._calculate_unique_count(data)
                elif metric == MetricType.NULL_COUNT:
                    result["null_count"] = self._calculate_null_count(data)
                elif metric == MetricType.PERCENTILE_25:
                    result["percentile_25"] = self._calculate_percentile(data, 25)
                elif metric == MetricType.PERCENTILE_75:
                    result["percentile_75"] = self._calculate_percentile(data, 75)
                elif metric == MetricType.PERCENTILE_90:
                    result["percentile_90"] = self._calculate_percentile(data, 90)
                elif metric == MetricType.PERCENTILE_95:
                    result["percentile_95"] = self._calculate_percentile(data, 95)
                elif metric == MetricType.CUSTOM:
                    result.update(self._calculate_custom_metrics(data))

            except Exception as e:
                logger.warning(f"Failed to calculate {metric}: {e}")
                result[metric] = np.nan

        return {"overall": result}

    def _calculate_grouped_metrics(
        self, data: pd.DataFrame, metrics: List[MetricType], grouping: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate metrics grouped by specified columns."""
        result = {}

        # Ensure grouping columns exist
        valid_grouping = [col for col in grouping if col in data.columns]
        if not valid_grouping:
            logger.warning(f"None of the grouping columns {grouping} found in data")
            return self._calculate_overall_metrics(data, metrics)

        # Group the data
        grouped = data.groupby(valid_grouping)

        for group_name, group_data in grouped:
            if isinstance(group_name, tuple):
                group_key = "_".join(str(x) for x in group_name)
            else:
                group_key = str(group_name)

            result[group_key] = {}

            for metric in metrics:
                try:
                    if metric == MetricType.MEAN:
                        result[group_key]["mean"] = self._calculate_mean(group_data)
                    elif metric == MetricType.MEDIAN:
                        result[group_key]["median"] = self._calculate_median(group_data)
                    elif metric == MetricType.MODE:
                        result[group_key]["mode"] = self._calculate_mode(group_data)
                    elif metric == MetricType.STD:
                        result[group_key]["std"] = self._calculate_std(group_data)
                    elif metric == MetricType.VARIANCE:
                        result[group_key]["variance"] = self._calculate_variance(
                            group_data
                        )
                    elif metric == MetricType.RANGE:
                        result[group_key]["range"] = self._calculate_range(group_data)
                    elif metric == MetricType.IQR:
                        result[group_key]["iqr"] = self._calculate_iqr(group_data)
                    elif metric == MetricType.SKEWNESS:
                        result[group_key]["skewness"] = self._calculate_skewness(
                            group_data
                        )
                    elif metric == MetricType.KURTOSIS:
                        result[group_key]["kurtosis"] = self._calculate_kurtosis(
                            group_data
                        )
                    elif metric == MetricType.COUNT:
                        result[group_key]["count"] = self._calculate_count(group_data)
                    elif metric == MetricType.UNIQUE_COUNT:
                        result[group_key]["unique_count"] = (
                            self._calculate_unique_count(group_data)
                        )
                    elif metric == MetricType.NULL_COUNT:
                        result[group_key]["null_count"] = self._calculate_null_count(
                            group_data
                        )
                    elif metric == MetricType.PERCENTILE_25:
                        result[group_key]["percentile_25"] = self._calculate_percentile(
                            group_data, 25
                        )
                    elif metric == MetricType.PERCENTILE_75:
                        result[group_key]["percentile_75"] = self._calculate_percentile(
                            group_data, 75
                        )
                    elif metric == MetricType.PERCENTILE_90:
                        result[group_key]["percentile_90"] = self._calculate_percentile(
                            group_data, 90
                        )
                    elif metric == MetricType.PERCENTILE_95:
                        result[group_key]["percentile_95"] = self._calculate_percentile(
                            group_data, 95
                        )
                    elif metric == MetricType.CUSTOM:
                        result[group_key].update(
                            self._calculate_custom_metrics(group_data)
                        )

                except Exception as e:
                    logger.warning(
                        f"Failed to calculate {metric} for group {group_key}: {e}"
                    )
                    result[group_key][metric] = np.nan

        return result

    def _calculate_mean(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate mean for numeric columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return {col: data[col].mean() for col in numeric_cols}

    def _calculate_median(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate median for numeric columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return {col: data[col].median() for col in numeric_cols}

    def _calculate_mode(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate mode for all columns."""
        result = {}
        for col in data.columns:
            mode_values = data[col].mode()
            if not mode_values.empty:
                result[col] = (
                    mode_values.iloc[0]
                    if len(mode_values) == 1
                    else mode_values.tolist()
                )
            else:
                result[col] = None
        return result

    def _calculate_std(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate standard deviation for numeric columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return {col: data[col].std() for col in numeric_cols}

    def _calculate_variance(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate variance for numeric columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return {col: data[col].var() for col in numeric_cols}

    def _calculate_range(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate range (max - min) for numeric columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return {col: data[col].max() - data[col].min() for col in numeric_cols}

    def _calculate_iqr(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate interquartile range for numeric columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return {
            col: data[col].quantile(0.75) - data[col].quantile(0.25)
            for col in numeric_cols
        }

    def _calculate_skewness(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate skewness for numeric columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return {col: skew(data[col].dropna()) for col in numeric_cols}

    def _calculate_kurtosis(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate kurtosis for numeric columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return {col: kurtosis(data[col].dropna()) for col in numeric_cols}

    def _calculate_count(self, data: pd.DataFrame) -> Dict[str, int]:
        """Calculate count for all columns."""
        return {col: len(data[col].dropna()) for col in data.columns}

    def _calculate_unique_count(self, data: pd.DataFrame) -> Dict[str, int]:
        """Calculate unique count for all columns."""
        return {col: data[col].nunique() for col in data.columns}

    def _calculate_null_count(self, data: pd.DataFrame) -> Dict[str, int]:
        """Calculate null count for all columns."""
        return {col: data[col].isnull().sum() for col in data.columns}

    def _calculate_percentile(
        self, data: pd.DataFrame, percentile: float
    ) -> Dict[str, float]:
        """Calculate specified percentile for numeric columns."""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        return {col: data[col].quantile(percentile / 100) for col in numeric_cols}

    def _calculate_custom_metrics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate custom metrics defined by the user."""
        result = {}

        for metric_name, expression in self._custom_metrics.items():
            try:
                # Simple expression evaluation - in production, you might want more sophisticated parsing
                if "mean(" in expression:
                    col = expression.replace("mean(", "").replace(")", "")
                    if col in data.columns:
                        result[metric_name] = data[col].mean()
                elif "median(" in expression:
                    col = expression.replace("median(", "").replace(")", "")
                    if col in data.columns:
                        result[metric_name] = data[col].median()
                elif "std(" in expression:
                    col = expression.replace("std(", "").replace(")", "")
                    if col in data.columns:
                        result[metric_name] = data[col].std()
                elif "count(" in expression:
                    col = expression.replace("count(", "").replace(")", "")
                    if col in data.columns:
                        result[metric_name] = len(data[col].dropna())
                elif "unique(" in expression:
                    col = expression.replace("unique(", "").replace(")", "")
                    if col in data.columns:
                        result[metric_name] = data[col].nunique()
                else:
                    # Try to evaluate as a pandas expression
                    result[metric_name] = data.eval(expression)

            except Exception as e:
                logger.warning(f"Failed to calculate custom metric {metric_name}: {e}")
                result[metric_name] = np.nan

        return result

    def calculate_correlation_matrix(
        self, data: pd.DataFrame, method: str = "pearson", min_periods: int = 1
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for numeric columns.

        Args:
            data: DataFrame to analyze
            method: Correlation method ('pearson', 'spearman', 'kendall')
            min_periods: Minimum number of observations required per pair of columns

        Returns:
            Correlation matrix as DataFrame
        """
        numeric_data = data.select_dtypes(include=[np.number])

        if numeric_data.empty:
            return pd.DataFrame()

        return numeric_data.corr(method=method, min_periods=min_periods)

    def calculate_summary_statistics(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive summary statistics for the dataset.

        Args:
            data: DataFrame to analyze

        Returns:
            Dictionary containing various summary statistics
        """
        if data.empty:
            return {}

        summary = {
            "shape": data.shape,
            "columns": list(data.columns),
            "dtypes": data.dtypes.to_dict(),
            "memory_usage": data.memory_usage(deep=True).to_dict(),
            "missing_values": data.isnull().sum().to_dict(),
            "missing_percentage": (data.isnull().sum() / len(data) * 100).to_dict(),
            "duplicate_rows": data.duplicated().sum(),
            "duplicate_percentage": (data.duplicated().sum() / len(data) * 100),
        }

        # Numeric summary
        numeric_data = data.select_dtypes(include=[np.number])
        if not numeric_data.empty:
            summary["numeric_summary"] = numeric_data.describe().to_dict()

            # Additional numeric statistics
            summary["numeric_stats"] = {
                "skewness": numeric_data.skew().to_dict(),
                "kurtosis": numeric_data.kurtosis().to_dict(),
                "iqr": (
                    numeric_data.quantile(0.75) - numeric_data.quantile(0.25)
                ).to_dict(),
            }

        # Categorical summary
        categorical_data = data.select_dtypes(include=["object", "category"])
        if not categorical_data.empty:
            summary["categorical_summary"] = {}
            for col in categorical_data.columns:
                value_counts = data[col].value_counts()
                summary["categorical_summary"][col] = {
                    "unique_count": value_counts.nunique(),
                    "top_values": value_counts.head(10).to_dict(),
                    "most_frequent": (
                        value_counts.index[0] if not value_counts.empty else None
                    ),
                }

        # Date summary
        date_columns = data.select_dtypes(include=["datetime64"]).columns
        if len(date_columns) > 0:
            summary["date_summary"] = {}
            for col in date_columns:
                summary["date_summary"][col] = {
                    "min_date": data[col].min(),
                    "max_date": data[col].max(),
                    "date_range_days": (
                        (data[col].max() - data[col].min()).days
                        if not data[col].empty
                        else 0
                    ),
                }

        return summary

    def calculate_distribution_metrics(
        self, data: pd.DataFrame, column: str, bins: int = 10
    ) -> Dict[str, Any]:
        """
        Calculate distribution metrics for a specific column.

        Args:
            data: DataFrame to analyze
            column: Column name to analyze
            bins: Number of bins for histogram

        Returns:
            Dictionary containing distribution metrics
        """
        if column not in data.columns:
            return {}

        col_data = data[column].dropna()
        if col_data.empty:
            return {}

        # Basic statistics
        distribution = {
            "count": len(col_data),
            "mean": col_data.mean(),
            "median": col_data.median(),
            "std": col_data.std(),
            "min": col_data.min(),
            "max": col_data.max(),
            "range": col_data.max() - col_data.min(),
            "iqr": col_data.quantile(0.75) - col_data.quantile(0.25),
            "skewness": skew(col_data),
            "kurtosis": kurtosis(col_data),
        }

        # Percentiles
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        distribution["percentiles"] = {
            f"p{p}": col_data.quantile(p / 100) for p in percentiles
        }

        # Histogram data
        if pd.api.types.is_numeric_dtype(col_data):
            hist, bin_edges = np.histogram(col_data, bins=bins)
            distribution["histogram"] = {
                "counts": hist.tolist(),
                "bin_edges": bin_edges.tolist(),
                "bin_centers": [
                    (bin_edges[i] + bin_edges[i + 1]) / 2
                    for i in range(len(bin_edges) - 1)
                ],
            }

        # Normality test (for numeric data)
        if pd.api.types.is_numeric_dtype(col_data) and len(col_data) >= 3:
            try:
                shapiro_stat, shapiro_p = stats.shapiro(col_data)
                distribution["normality_test"] = {
                    "shapiro_w": shapiro_stat,
                    "shapiro_p": shapiro_p,
                    "is_normal": shapiro_p > 0.05,
                }
            except Exception as e:
                logger.warning(f"Could not perform normality test on {column}: {e}")

        return distribution

    def add_custom_metric(self, name: str, expression: str) -> None:
        """Add a custom metric definition."""
        self._custom_metrics[name] = expression

    def remove_custom_metric(self, name: str) -> None:
        """Remove a custom metric definition."""
        self._custom_metrics.pop(name, None)

    def list_custom_metrics(self) -> List[str]:
        """List all custom metric names."""
        return list(self._custom_metrics.keys())

    def clear_custom_metrics(self) -> None:
        """Clear all custom metric definitions."""
        self._custom_metrics.clear()
