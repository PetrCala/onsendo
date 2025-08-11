"""
mock_data.py

Mass insert mock onsen visit data into the database for testing purposes.
"""

import argparse
from loguru import logger
from src.db.conn import get_db
from src.db.models import OnsenVisit, Onsen
from src.testing.mocks.mock_visit_data import (
    MockVisitDataGenerator,
    create_realistic_visit_scenario,
    create_visit_series,
    create_seasonal_visits,
)
from src.const import CONST


def insert_mock_data(args: argparse.Namespace) -> None:
    """
    Insert mock onsen visit data into the database.
    """
    with get_db(url=CONST.DATABASE_URL) as db:
        # Check if there are any onsens in the database
        onsen_count = db.query(Onsen).count()
        if onsen_count == 0:
            logger.error("No onsens found in database! Please add some onsens first.")
            return

        # Get available onsen IDs
        onsen_ids = [onsen.id for onsen in db.query(Onsen).all()]
        logger.info(f"Found {onsen_count} onsens in database with IDs: {onsen_ids}")

        # Generate mock data based on scenario type
        if args.scenario == "random":
            visits = create_realistic_visit_scenario(
                onsen_ids=onsen_ids,
                scenario_type="random",
                num_days=args.num_days,
                visits_per_day=args.visits_per_day,
            )
        elif args.scenario == "weekend_warrior":
            visits = create_realistic_visit_scenario(
                onsen_ids=onsen_ids,
                scenario_type="weekend_warrior",
            )
        elif args.scenario == "daily_visitor":
            visits = create_realistic_visit_scenario(
                onsen_ids=onsen_ids,
                scenario_type="daily_visitor",
            )
        elif args.scenario == "seasonal_explorer":
            visits = create_realistic_visit_scenario(
                onsen_ids=onsen_ids,
                scenario_type="seasonal_explorer",
            )
        elif args.scenario == "multi_onsen_enthusiast":
            visits = create_realistic_visit_scenario(
                onsen_ids=onsen_ids,
                scenario_type="multi_onsen_enthusiast",
            )
        elif args.scenario == "custom":
            generator = MockVisitDataGenerator()
            start_date = None
            if args.start_date:
                from datetime import datetime

                try:
                    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
                except ValueError:
                    logger.error(
                        f"Invalid date format: {args.start_date}. Use YYYY-MM-DD format."
                    )
                    return

            visits = generator.generate_visit_series(
                onsen_ids=onsen_ids,
                num_days=args.num_days,
                visits_per_day=args.visits_per_day,
                start_date=start_date,
            )
        elif args.scenario == "seasonal":
            visits = create_seasonal_visits(
                onsen_ids=onsen_ids,
                season=args.season,
                num_visits=args.num_visits,
            )
        else:
            logger.error(f"Unknown scenario: {args.scenario}")
            return

        logger.info(f"Generated {len(visits)} mock visits")

        # Convert mock data to database models
        db_visits = []
        for visit in visits:
            db_visit = OnsenVisit(
                onsen_id=visit.onsen_id,
                entry_fee_yen=visit.entry_fee_yen,
                payment_method=visit.payment_method,
                weather=visit.weather,
                time_of_day=visit.time_of_day,
                temperature_outside_celsius=visit.temperature_outside_celsius,
                visit_time=visit.visit_time,
                stay_length_minutes=visit.stay_length_minutes,
                visited_with=visit.visited_with,
                travel_mode=visit.travel_mode,
                travel_time_minutes=visit.travel_time_minutes,
                accessibility_rating=visit.accessibility_rating,
                exercise_before_onsen=visit.exercise_before_onsen,
                exercise_type=visit.exercise_type,
                exercise_length_minutes=visit.exercise_length_minutes,
                crowd_level=visit.crowd_level,
                view_rating=visit.view_rating,
                navigability_rating=visit.navigability_rating,
                cleanliness_rating=visit.cleanliness_rating,
                main_bath_type=visit.main_bath_type,
                main_bath_temperature=visit.main_bath_temperature,
                main_bath_water_type=visit.main_bath_water_type,
                water_color=visit.water_color,
                smell_intensity_rating=visit.smell_intensity_rating,
                changing_room_cleanliness_rating=visit.changing_room_cleanliness_rating,
                locker_availability_rating=visit.locker_availability_rating,
                had_soap=visit.had_soap,
                had_sauna=visit.had_sauna,
                had_outdoor_bath=visit.had_outdoor_bath,
                had_rest_area=visit.had_rest_area,
                rest_area_used=visit.rest_area_used,
                rest_area_rating=visit.rest_area_rating,
                had_food_service=visit.had_food_service,
                food_service_used=visit.food_service_used,
                food_quality_rating=visit.food_quality_rating,
                massage_chair_available=visit.massage_chair_available,
                sauna_visited=visit.sauna_visited,
                sauna_temperature=visit.sauna_temperature,
                sauna_steam=visit.sauna_steam,
                sauna_duration_minutes=visit.sauna_duration_minutes,
                sauna_rating=visit.sauna_rating,
                outdoor_bath_visited=visit.outdoor_bath_visited,
                outdoor_bath_temperature=visit.outdoor_bath_temperature,
                outdoor_bath_rating=visit.outdoor_bath_rating,
                pre_visit_mood=visit.pre_visit_mood,
                post_visit_mood=visit.post_visit_mood,
                energy_level_change=visit.energy_level_change,
                hydration_level=visit.hydration_level,
                previous_location=visit.previous_location,
                next_location=visit.next_location,
                multi_onsen_day=visit.multi_onsen_day,
                visit_order=visit.visit_order,
                atmosphere_rating=visit.atmosphere_rating,
                personal_rating=visit.personal_rating,
            )
            db_visits.append(db_visit)

        # Insert all visits
        db.add_all(db_visits)
        db.commit()

        logger.info(f"Successfully inserted {len(db_visits)} mock visits into database")

        # Show some statistics
        if db_visits:
            total_rating = sum(visit.personal_rating for visit in db_visits)
            avg_rating = total_rating / len(db_visits)
            logger.info(f"Average personal rating: {avg_rating:.1f}/10")

            # Count multi-onsen days
            multi_onsen_count = sum(1 for visit in db_visits if visit.multi_onsen_day)
            if multi_onsen_count > 0:
                logger.info(f"Multi-onsen days: {multi_onsen_count}")

            # Show date range
            dates = [visit.visit_time.date() for visit in db_visits]
            min_date = min(dates)
            max_date = max(dates)
            logger.info(f"Date range: {min_date} to {max_date}")


def get_available_scenarios() -> list:
    """Get list of available mock data scenarios."""
    return [
        "random",
        "weekend_warrior",
        "daily_visitor",
        "seasonal_explorer",
        "multi_onsen_enthusiast",
        "custom",
        "seasonal",
    ]
