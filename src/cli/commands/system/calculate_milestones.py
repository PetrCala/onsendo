"""
CLI command to calculate distance milestones for a location.
"""

from sqlalchemy.orm import Session

from src.db.models import Location
from src.lib.milestone_calculator import (
    analyze_location_distances,
    print_milestone_analysis,
)
from src.lib.recommendation import OnsenRecommendationEngine


def calculate_milestones(args):
    """
    Calculate distance milestones for a location based on onsen distribution.
    """
    location_identifier = args.location_identifier
    update_engine = args.update_engine
    show_recommendations = args.show_recommendations

    from src.db.conn import get_db_from_args
    
# Get database configuration
    with get_db_from_args(args) as db:
        # Find the location
        location = _get_location_by_identifier(db, location_identifier)
        if not location:
            print(f"Location '{location_identifier}' not found.")
            return

        print(f"Calculating milestones for location: {location.name}")
        print("=" * 50)

        # Analyze the location
        analysis = analyze_location_distances(location, db)

        if "error" in analysis:
            print(f"Error: {analysis['error']}")
            return

        # Print the analysis
        print_milestone_analysis(analysis)

        if update_engine:
            print("\n" + "=" * 50)
            print("UPDATING RECOMMENDATION ENGINE")
            print("=" * 50)

            # Create recommendation engine with the location
            engine = OnsenRecommendationEngine(db, location)

            print("Recommendation engine updated with new milestones:")
            engine.print_distance_milestones()

            if show_recommendations:
                print("\n" + "=" * 50)
                print("SAMPLE RECOMMENDATIONS")
                print("=" * 50)

                for category in ["very_close", "close", "medium", "far"]:
                    recommendations = engine.recommend_onsens(
                        location=location, distance_category=category, limit=5
                    )

                    print(f"\n{category.upper()} onsens (limit 5):")
                    if recommendations:
                        for onsen, distance, _ in recommendations:
                            print(f"  - {onsen.name}: {distance:.2f} km")
                    else:
                        print(f"  No onsens found in {category} category")


def _get_location_by_identifier(db: Session, identifier: str) -> Location:
    """Get a location by name or ID."""
    # Try to parse as ID first
    try:
        location_id = int(identifier)
        return db.query(Location).filter(Location.id == location_id).first()
    except ValueError:
        pass

    # Try to find by name
    return db.query(Location).filter(Location.name == identifier).first()
