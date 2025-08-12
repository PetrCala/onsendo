"""
list_scenarios.py

List available analysis scenarios.
"""

import argparse

from src.types.analysis import AnalysisScenario, ANALYSIS_SCENARIOS


def list_scenarios(args: argparse.Namespace) -> None:
    """List available analysis scenarios."""
    print("Available Analysis Scenarios:")
    print("=" * 50)

    for scenario in AnalysisScenario:
        if scenario in ANALYSIS_SCENARIOS:
            config = ANALYSIS_SCENARIOS[scenario]
            print(f"\n{scenario.value.upper()}")
            print(f"  Description: {config.description}")
            print(
                f"  Analysis Types: {', '.join([t.value for t in config.analysis_types])}"
            )
            print(
                f"  Data Categories: {', '.join([c.value for c in config.data_categories])}"
            )
            print(f"  Metrics: {', '.join([m.value for m in config.metrics])}")
            print(
                f"  Visualizations: {', '.join([v.value for v in config.visualizations])}"
            )
            if config.models:
                print(f"  Models: {', '.join([m.value for m in config.models])}")
            print(f"  Focus Areas: {', '.join(config.insights_focus)}")
