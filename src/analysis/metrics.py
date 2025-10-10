"""
Metrics calculation system for onsen analysis - simplified for essential statistics.

For detailed statistical analysis, use:
- EconometricAnalyzer from src.analysis.econometrics for regression
- InsightDiscovery from src.analysis.insight_discovery for pattern detection
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import skew, kurtosis

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Calculator for summary statistics and correlations.
    """

    def calculate_summary_statistics(self, data: pd.DataFrame) -> dict[str, Any]:
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
            "dtypes": {str(k): str(v) for k, v in data.dtypes.to_dict().items()},
            "memory_usage": {str(k): int(v) for k, v in data.memory_usage(deep=True).to_dict().items()},
            "missing_values": {str(k): int(v) for k, v in data.isnull().sum().to_dict().items()},
            "missing_percentage": {str(k): float(v) for k, v in (data.isnull().sum() / len(data) * 100).to_dict().items()},
            "duplicate_rows": int(data.duplicated().sum()),
            "duplicate_percentage": float(data.duplicated().sum() / len(data) * 100),
        }

        # Numeric summary
        numeric_data = data.select_dtypes(include=[np.number])
        if not numeric_data.empty:
            # Convert to dict with string keys
            summary["numeric_summary"] = {
                str(k): {str(k2): float(v2) if not pd.isna(v2) else None for k2, v2 in v.items()}
                for k, v in numeric_data.describe().to_dict().items()
            }

            # Additional numeric statistics
            summary["numeric_stats"] = {
                "skewness": {str(k): float(v) if not pd.isna(v) else None for k, v in numeric_data.skew().to_dict().items()},
                "kurtosis": {str(k): float(v) if not pd.isna(v) else None for k, v in numeric_data.kurtosis().to_dict().items()},
                "iqr": {
                    str(k): float(v) if not pd.isna(v) else None
                    for k, v in (numeric_data.quantile(0.75) - numeric_data.quantile(0.25)).to_dict().items()
                },
            }

        # Categorical summary
        categorical_data = data.select_dtypes(include=["object", "category"])
        if not categorical_data.empty:
            summary["categorical_summary"] = {}
            for col in categorical_data.columns:
                value_counts = data[col].value_counts()
                summary["categorical_summary"][str(col)] = {
                    "unique_count": int(value_counts.nunique()),
                    "top_values": {str(k): int(v) for k, v in value_counts.head(10).to_dict().items()},
                    "most_frequent": (
                        str(value_counts.index[0]) if not value_counts.empty else None
                    ),
                }

        # Date summary
        date_columns = data.select_dtypes(include=["datetime64"]).columns
        if len(date_columns) > 0:
            summary["date_summary"] = {}
            for col in date_columns:
                summary["date_summary"][col] = {
                    "min_date": str(data[col].min()),
                    "max_date": str(data[col].max()),
                    "date_range_days": int(
                        (data[col].max() - data[col].min()).days
                        if not data[col].isnull().all()
                        else 0
                    ),
                }

        return summary

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

    def calculate_distribution_metrics(
        self, data: pd.DataFrame, column: str, bins: int = 10
    ) -> dict[str, Any]:
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
            "count": int(len(col_data)),
            "mean": float(col_data.mean()),
            "median": float(col_data.median()),
            "std": float(col_data.std()),
            "min": float(col_data.min()),
            "max": float(col_data.max()),
            "range": float(col_data.max() - col_data.min()),
            "iqr": float(col_data.quantile(0.75) - col_data.quantile(0.25)),
            "skewness": float(skew(col_data)),
            "kurtosis": float(kurtosis(col_data)),
        }

        # Percentiles
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        distribution["percentiles"] = {
            f"p{p}": float(col_data.quantile(p / 100)) for p in percentiles
        }

        # Histogram data
        if pd.api.types.is_numeric_dtype(col_data):
            hist, bin_edges = np.histogram(col_data, bins=bins)
            distribution["histogram"] = {
                "counts": hist.tolist(),
                "bin_edges": bin_edges.tolist(),
                "bin_centers": [
                    float((bin_edges[i] + bin_edges[i + 1]) / 2)
                    for i in range(len(bin_edges) - 1)
                ],
            }

        # Normality test (for numeric data)
        if pd.api.types.is_numeric_dtype(col_data) and len(col_data) >= 3:
            try:
                shapiro_stat, shapiro_p = stats.shapiro(col_data)
                distribution["normality_test"] = {
                    "shapiro_w": float(shapiro_stat),
                    "shapiro_p": float(shapiro_p),
                    "is_normal": bool(shapiro_p > 0.05),
                }
            except (ValueError, RuntimeWarning) as e:
                logger.warning(f"Could not perform normality test on {column}: {e}")

        return distribution

    def get_numeric_summary(self, data: pd.DataFrame) -> dict[str, dict[str, float]]:
        """
        Get quick numeric summary for all numeric columns.

        Args:
            data: DataFrame to analyze

        Returns:
            Dictionary of numeric summaries
        """
        numeric_data = data.select_dtypes(include=[np.number])

        if numeric_data.empty:
            return {}

        summary = {}
        for col in numeric_data.columns:
            col_data = numeric_data[col].dropna()
            if len(col_data) > 0:
                summary[col] = {
                    "count": int(len(col_data)),
                    "mean": float(col_data.mean()),
                    "std": float(col_data.std()),
                    "min": float(col_data.min()),
                    "25%": float(col_data.quantile(0.25)),
                    "50%": float(col_data.median()),
                    "75%": float(col_data.quantile(0.75)),
                    "max": float(col_data.max()),
                }

        return summary
