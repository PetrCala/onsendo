"""Graphing system for generating visualizations and dashboards.

This module provides a scalable, maintainable system for generating graphs
from various data sources (visits, weight, exercise, etc.).
"""

from src.lib.graphing.base import (
    DataSource,
    DashboardConfig,
    GraphCategory,
    GraphDefinition,
    GraphType,
)

__all__ = [
    "GraphType",
    "DataSource",
    "GraphCategory",
    "GraphDefinition",
    "DashboardConfig",
]
