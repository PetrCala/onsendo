"""
Recommend onsen command with interactive support.
"""

import argparse
import webbrowser
from datetime import datetime
from pathlib import Path
from src.db.conn import get_db_from_args
from src.lib.recommendation import OnsenRecommendationEngine
from src.lib.map_generator import generate_recommendation_map


def recommend_onsen(args: argparse.Namespace) -> None:
    """Get onsen recommendations based on location and criteria."""
    if not hasattr(args, "no_interactive") or not args.no_interactive:
        recommend_onsen_interactive(args)
        return

    # Use database session
    with get_db_from_args(args) as db:
        # Get the location first
        engine_temp = OnsenRecommendationEngine(db)
        location = engine_temp.get_location_by_name_or_id(args.location)
        if not location:
            print(f"Error: Location '{args.location}' not found.")
            print("Use 'list-locations' to see available locations.")
            return

        # Create recommendation engine with the location to calculate dynamic milestones
        engine = OnsenRecommendationEngine(db, location)

        # Parse target time if provided
        target_time = None
        if args.time:
            try:
                target_time = datetime.strptime(args.time, "%Y-%m-%d %H:%M")
            except ValueError:
                print("Error: Invalid time format. Use YYYY-MM-DD HH:MM")
                return

        # Get recommendations
        recommendations = engine.recommend_onsens(
            location=location,
            target_time=target_time,
            distance_category=args.distance,
            exclude_closed=args.exclude_closed,
            exclude_visited=args.exclude_visited,
            min_hours_after=args.min_hours_after,
            limit=args.limit,
            stay_restriction_filter=args.stay_restriction_filter,
        )

        # Display results
        if not recommendations:
            print("No onsens found matching your criteria.")
            return

        print(f"Found {len(recommendations)} onsen(s) matching your criteria:")
        print(f"Location: {location.name}")
        print(f"Distance: {args.distance}")
        print(f"Time: {target_time or 'now'}")
        print(f"Exclude closed: {args.exclude_closed}")
        print(f"Exclude visited: {args.exclude_visited}")
        if args.min_hours_after:
            print(f"Minimum hours after target time: {args.min_hours_after}")
        if args.stay_restriction_filter:
            print(f"Stay restriction filter: {args.stay_restriction_filter}")
        print()

        for i, (onsen, distance, metadata) in enumerate(recommendations, 1):
            print(f"{i}. {onsen.name} (ID: {onsen.id}, BAN: {onsen.ban_number})")
            print(f"   Distance: {distance:.1f} km ({metadata['distance_category']})")
            print(f"   Address: {onsen.address or 'N/A'}")
            print(f"   Maps: {metadata['google_maps_link']}")
            if onsen.usage_time:
                print(f"   Hours: {onsen.usage_time}")
            if onsen.admission_fee:
                print(f"   Fee: {onsen.admission_fee}")
            if metadata["has_been_visited"]:
                print(f"   Status: Previously visited")
            if metadata["stay_restricted"]:
                print(
                    f"   Stay restriction: {'Yes' if metadata['stay_restricted'] else 'No'}"
                )
                if metadata["stay_restriction_notes"]:
                    for note in metadata["stay_restriction_notes"]:
                        print(f"     Note: {note}")
            print()

        # Generate interactive map by default (unless disabled)
        should_generate_map = not (hasattr(args, "no_generate_map") and args.no_generate_map)
        if hasattr(args, "generate_map"):
            should_generate_map = args.generate_map

        if should_generate_map:
            try:
                map_path = generate_recommendation_map(
                    recommendations, location
                )
                print("=" * 60)
                print("Interactive Map Generated!")
                print(f"\nMap saved to: {map_path}")

                # Check if auto-open is requested
                auto_open = getattr(args, "open_map", False)
                if auto_open:
                    print("\nOpening map in browser...")
                    webbrowser.open(Path(map_path).as_uri())
                else:
                    print("\nTo open in browser, click the link below:")
                    print(f"{Path(map_path).as_uri()}")
                    print(f"\nOr run: open '{map_path}'")
                    print("Tip: Use --open_map flag to automatically open in browser")
                print("=" * 60)
            except (OSError, ValueError) as e:
                print(f"Error generating map: {e}")


def recommend_onsen_interactive(args: argparse.Namespace) -> None:
    """Get onsen recommendations using interactive prompts."""
    print("=== Onsen Recommendation ===")

    # Use database session
    with get_db_from_args(args) as db:
        engine_temp = OnsenRecommendationEngine(db)

        # List available locations
        locations = engine_temp.list_locations()
        if not locations:
            print(
                "No locations found. Please add a location first using 'location add'."
            )
            return

        print("Available locations:")
        for location in locations:
            print(f"  {location.id}: {location.name}")
        print()

        # Get location
        while True:
            location_input = input("Enter location ID or name: ").strip()
            if location_input:
                location = engine_temp.get_location_by_name_or_id(location_input)
                if location:
                    break
                print("Location not found. Please try again.")
            else:
                print("Location is required.")

        # Create recommendation engine with the location to calculate dynamic milestones
        engine = OnsenRecommendationEngine(db, location)

        # Get distance milestones for display in the prompt
        distance_milestones = engine.get_distance_milestones()

        # Get target time
        time_input = input(
            "Target time (YYYY-MM-DD HH:MM, or press Enter for now): "
        ).strip()
        target_time = None
        if time_input:
            try:
                target_time = datetime.strptime(time_input, "%Y-%m-%d %H:%M")
            except ValueError:
                print("Invalid time format. Using current time.")

        # Get distance category
        print("\nDistance categories:")
        if distance_milestones:
            print(f"  1: Very close (≤ {distance_milestones.very_close_max:.1f} km)")
            print(f"  2: Close (≤ {distance_milestones.close_max:.1f} km)")
            print(f"  3: Medium (≤ {distance_milestones.medium_max:.1f} km)")
            print(f"  4: Far (> {distance_milestones.medium_max:.1f} km)")
            print(f"  5: Any distance")
        else:
            print("  1: Very close (≤ 5.0 km)")
            print("  2: Close (≤ 15.0 km)")
            print("  3: Medium (≤ 50.0 km)")
            print("  4: Far (> 50.0 km)")
            print(f"  5: Any distance")

        while True:
            distance_choice = input("Choose distance category (1-5): ").strip()
            distance_map = {"1": "very_close", "2": "close", "3": "medium", "4": "far", "5": "any"}
            if distance_choice in distance_map:
                distance_category = distance_map[distance_choice]
                break
            print("Please enter a number between 1 and 5.")

        # Get filters
        exclude_closed = (
            input("Exclude closed onsens? (y/n, default: y): ").strip().lower() != "n"
        )
        exclude_visited = (
            input("Exclude visited onsens? (y/n, default: y): ").strip().lower() != "n"
        )

        # Get stay restriction filter
        print("\nStay restriction filter:")
        print("  1: Non-stay-restricted only (exclude 宿泊限定 onsens)")
        print("  2: All onsens (include stay-restricted)")

        while True:
            stay_filter_choice = input(
                "Choose stay restriction filter (1-2, default: 1): "
            ).strip()
            if not stay_filter_choice:
                stay_restriction_filter = "non_stay_restricted"
                break
            elif stay_filter_choice == "1":
                stay_restriction_filter = "non_stay_restricted"
                break
            elif stay_filter_choice == "2":
                stay_restriction_filter = "all"
                break
            else:
                print("Please enter 1 or 2.")

        # Get minimum hours after target time
        min_hours_input = input(
            "Minimum hours onsen should be open after target time (press Enter for 2, or 0 to disable): "
        ).strip()
        min_hours_after = 2  # default
        if min_hours_input:
            try:
                min_hours_after = int(min_hours_input)
                if min_hours_after < 0:
                    print("Invalid number. Using default of 2 hours.")
                    min_hours_after = 2
            except ValueError:
                print("Invalid number. Using default of 2 hours.")
                min_hours_after = 2

        # Get limit
        limit_input = input(
            "Maximum number of recommendations (press Enter for no limit): "
        ).strip()
        limit = None
        if limit_input:
            try:
                limit = int(limit_input)
            except ValueError:
                print("Invalid number. No limit will be applied.")

        # Ask about interactive map generation
        generate_map_input = input(
            "Generate interactive map? (y/n, default: y): "
        ).strip().lower()
        generate_map = generate_map_input != "n"

        # Ask about auto-opening if map will be generated
        open_map = False
        if generate_map:
            open_map_input = input(
                "Automatically open map in browser? (y/n, default: y): "
            ).strip().lower()
            open_map = open_map_input != "n"

        # Create args object for the main function
        class Args:
            pass

        args = Args()
        args.location = location.name
        args.time = time_input if time_input else None
        args.distance = distance_category
        args.exclude_closed = exclude_closed
        args.exclude_visited = exclude_visited
        args.stay_restriction_filter = stay_restriction_filter
        args.min_hours_after = min_hours_after if min_hours_after > 0 else None
        args.limit = limit
        args.generate_map = generate_map
        args.open_map = open_map
        args.no_interactive = True

        recommend_onsen(args)
