"""
run_scenario_analysis.py

Run a predefined analysis scenario.
"""

import argparse
import json

from loguru import logger

from src.const import CONST
from src.db.conn import get_db
from src.analysis.engine import AnalysisEngine
from src.types.analysis import AnalysisScenario, ANALYSIS_SCENARIOS


def run_scenario_analysis(args: argparse.Namespace) -> None:
    """Run a predefined analysis scenario."""
    # Check if we should run in interactive mode
    if not hasattr(args, "no_interactive") or not args.no_interactive:
        if not args.scenario:
            run_scenario_analysis_interactive(args)
            return

    # Validate required arguments in non-interactive mode
    if not args.scenario:
        logger.error("scenario is required in non-interactive mode")
        print("Error: scenario is required. Use --help for more information.")
        return

    try:
        with get_db(url=CONST.DATABASE_URL) as session:
            # Initialize analysis engine
            engine = AnalysisEngine(session, args.output_dir)

            # Parse scenario
            try:
                scenario = AnalysisScenario(args.scenario)
            except ValueError:
                logger.error(f"Unknown scenario: {args.scenario}")
                print(
                    f"Available scenarios: {', '.join([s.value for s in AnalysisScenario])}"
                )
                return

            # Econometric scenarios use the new econometric analysis engine
            econometric_scenarios = [
                AnalysisScenario.ENJOYMENT_DRIVERS,
                AnalysisScenario.PRICING_OPTIMIZATION,
            ]

            if scenario in econometric_scenarios:
                # Use econometric analysis engine for professional analysis
                logger.info(f"Running econometric scenario: {scenario.value}")
                scenario_config = ANALYSIS_SCENARIOS[scenario]

                result = engine.run_econometric_analysis(
                    dependent_var='personal_rating',
                    data_categories=scenario_config.data_categories,
                    max_models=20,
                    analysis_name=scenario_config.description,
                )

                if result['status'] == 'error':
                    logger.error(f"Econometric analysis failed: {result['error']}")
                    print(f"\nError: {result['error']}")
                else:
                    logger.info("Econometric analysis completed successfully!")
                    print(f"\n✅ Analysis complete in {result['execution_time']:.1f}s")
                    print(f"📊 Estimated {result['n_models_estimated']} models")
                    print(f"💡 Discovered {result['n_insights_discovered']} insights")

                    if result['best_model']['name']:
                        print(f"\n🏆 Best model: {result['best_model']['name']}")
                        print(f"   Adjusted R²: {result['best_model']['adj_r2']:.3f}")
                        print(f"   Quality: {result['best_model']['quality']}")

                    print(f"\n📁 Output directory: {result['output_directory']}")
                    print(f"📄 Report: {result['report_path']}")
                    print(f"\n🌐 Open report in browser:")
                    print(f"   file://{result['report_path']}")

                    if result['map_files']:
                        print(f"\n🗺️  Interactive maps:")
                        for map_type, map_path in result['map_files'].items():
                            print(f"   {map_type}: file://{map_path}")

            else:
                # Use standard analysis engine for basic scenarios
                # Parse custom configuration
                custom_config = None
                if args.custom_config:
                    try:
                        custom_config = json.loads(args.custom_config)
                    except json.JSONDecodeError:
                        logger.error("Invalid JSON in custom_config")
                        return

                logger.info(f"Running scenario: {scenario.value}")
                result = engine.run_scenario_analysis(scenario, custom_config)

                if result.errors:
                    logger.error("Scenario analysis completed with errors:")
                    for error in result.errors:
                        logger.error(f"  - {error}")
                        print(f"\nError: {error}")
                else:
                    logger.info("Scenario analysis completed successfully!")
                    logger.info(f"Generated {len(result.visualizations)} visualizations")
                    logger.info(f"Generated {len(result.insights)} insights")
                    if result.models:
                        logger.info(f"Trained {len(result.models)} models")

                    # Print scenario-specific summaries
                    if scenario == AnalysisScenario.OVERVIEW:
                        # Print comprehensive overview summary
                        overview_summary = engine.generate_overview_summary(result)
                        print(overview_summary)
                    elif scenario == AnalysisScenario.SPATIAL_ANALYSIS:
                        # Print spatial analysis summary
                        print(f"\n✅ Spatial analysis complete in {result.execution_time:.1f}s")
                        print(f"📊 Analyzed {len(result.data)} locations")
                        print(f"🗺️  Generated {len(result.visualizations)} maps")
                        if result.models:
                            print(f"🔍 Identified spatial clusters using {len(result.models)} models")
                        print(f"\n📁 Output directory: {result.metadata.get('output_directory', 'N/A')}")
                    elif scenario == AnalysisScenario.TEMPORAL_ANALYSIS:
                        # Print temporal analysis summary
                        print(f"\n✅ Temporal analysis complete in {result.execution_time:.1f}s")
                        print(f"📊 Analyzed {len(result.data)} time points")
                        print(f"📈 Generated {len(result.visualizations)} trend visualizations")
                        print(f"\n📁 Output directory: {result.metadata.get('output_directory', 'N/A')}")
                    else:
                        # Generic summary for other scenarios
                        print(f"\n✅ Analysis complete in {result.execution_time:.1f}s")
                        print(f"📊 Processed {len(result.data)} records")
                        print(f"📈 Generated {len(result.visualizations)} visualizations")
                        if result.insights:
                            print(f"💡 Discovered {len(result.insights)} insights")
                        print(f"\n📁 Output directory: {result.metadata.get('output_directory', 'N/A')}")

                    # Print insights for non-overview scenarios
                    if scenario != AnalysisScenario.OVERVIEW and result.insights:
                        print("\n=== Analysis Insights ===")
                        for i, insight in enumerate(result.insights, 1):
                            print(f"{i}. {insight}")

                    # Export results if requested
                    if args.export:
                        export_path = engine.export_results(result, args.export)
                        if export_path:
                            print(f"\nResults exported to: {export_path}")

    except Exception as e:
        logger.error(f"Scenario analysis failed: {e}")
        raise


def run_scenario_analysis_interactive(args: argparse.Namespace) -> None:
    """Run scenario analysis with interactive prompts for missing parameters."""
    print("=== Run Analysis Scenario ===\n")

    # Display available scenarios with descriptions
    print("Available Analysis Scenarios:")
    scenarios = []
    for scenario in AnalysisScenario:
        if scenario in ANALYSIS_SCENARIOS:
            config = ANALYSIS_SCENARIOS[scenario]
            scenarios.append(scenario)
            print(f"\n  {len(scenarios)}. {scenario.value.upper()}")
            print(f"     {config.description}")

    # Prompt for scenario
    while True:
        selection = input("\nSelect scenario (number or name): ").strip()

        # Try to parse as number
        if selection.isdigit():
            idx = int(selection) - 1
            if 0 <= idx < len(scenarios):
                selected_scenario = scenarios[idx].value
                break
            else:
                print(f"Invalid selection. Please enter a number between 1 and {len(scenarios)}.")
                continue

        # Try to match by name
        try:
            AnalysisScenario(selection)
            selected_scenario = selection
            break
        except ValueError:
            print(f"Invalid scenario: {selection}")
            print("Please enter a valid scenario name or number.")

    # Update args and call main function
    args.scenario = selected_scenario
    args.no_interactive = True

    print(f"\nRunning {selected_scenario} scenario...")
    run_scenario_analysis(args)
