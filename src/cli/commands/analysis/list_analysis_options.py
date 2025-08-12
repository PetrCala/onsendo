"""
list_analysis_options.py

List available analysis options.
"""

import argparse

from src.types.analysis import (
    AnalysisType,
    DataCategory,
    MetricType,
    VisualizationType,
    ModelType,
)


def list_analysis_options(args: argparse.Namespace) -> None:
    """List available analysis options."""
    print("Available Analysis Options:")
    print("=" * 50)

    print("\nAnalysis Types:")
    for analysis_type in AnalysisType:
        print(f"  - {analysis_type.value}")

    print("\nData Categories:")
    for category in DataCategory:
        print(f"  - {category.value}")

    print("\nMetrics:")
    for metric in MetricType:
        print(f"  - {metric.value}")

    print("\nVisualizations:")
    for viz in VisualizationType:
        print(f"  - {viz.value}")

    print("\nModels:")
    for model in ModelType:
        print(f"  - {model.value}")
