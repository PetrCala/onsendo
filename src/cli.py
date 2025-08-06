"""
cli.py

A simple CLI to demonstrate how you might add or update onsen data
or add onsen visits. You could use argparse or click for a nicer interface.
"""

import argparse
from loguru import logger
from sqlalchemy.orm import Session
from src.db.conn import SessionLocal
from src.db.models import Onsen, OnsenVisit


def add_onsen(args):
    with SessionLocal() as db:
        onsen = Onsen(
            ban_number=args.ban_number,
            name=args.name,
            address=args.address,
            # ...
        )
        db.add(onsen)
        db.commit()
        logger.info(f"Added onsen {onsen.name}")


def add_visit(args):
    with SessionLocal() as db:
        # fetch the onsen
        onsen = db.query(Onsen).filter(Onsen.id == args.onsen_id).first()
        if not onsen:
            logger.error(f"No onsen with id={args.onsen_id} found!")
            return

        visit = OnsenVisit(
            onsen_id=onsen.id,
            entry_fee_yen=args.entry_fee_yen,
            payment_method=args.payment_method,
            weather=args.weather,
            time_of_day=args.time_of_day,
            temperature_outside_celsius=args.temperature_outside_celsius,
            visit_time=args.visit_time,
            stay_length_minutes=args.stay_length_minutes,
            visited_with=args.visited_with,
            travel_mode=args.travel_mode,
            travel_time_minutes=args.travel_time_minutes,
            accessibility_rating=args.accessibility_rating,
            excercise_before_onsen=args.excercise_before_onsen,
            excercise_type=args.excercise_type,
            excercise_length_minutes=args.excercise_length_minutes,
            crowd_level=args.crowd_level,
            heart_rate_data=args.heart_rate_data,
            cleanliness_rating=args.cleanliness_rating,
            navigability_rating=args.navigability_rating,
            view_rating=args.view_rating,
            main_bath_type=args.main_bath_type,
            main_bath_temperature=args.main_bath_temperature,
            main_bath_water_type=args.main_bath_water_type,
            water_color=args.water_color,
            smell_intensity_rating=args.smell_intensity_rating,
            changing_room_cleanliness_rating=args.changing_room_cleanliness_rating,
            locker_availability_rating=args.locker_availability_rating,
            had_soap=args.had_soap,
            had_sauna=args.had_sauna,
            had_outdoor_bath=args.had_outdoor_bath,
            had_rest_area=args.had_rest_area,
            had_food_service=args.had_food_service,
            rest_area_rating=args.rest_area_rating,
            food_quality_rating=args.food_quality_rating,
            massage_chair_available=args.massage_chair_available,
            outdoor_bath_visited=args.outdoor_bath_visited,
            outdoor_bath_temperature=args.outdoor_bath_temperature,
            sauna_visited=args.sauna_visited,
            sauna_temperature=args.sauna_temperature,
            sauna_steam=args.sauna_steam,
            sauna_duration_minutes=args.sauna_duration_minutes,
            sauna_rating=args.sauna_rating,
            had_outdoor_bath=args.had_outdoor_bath,
            outdoor_bath_visited=args.outdoor_bath_visited,
            outdoor_bath_temperature=args.outdoor_bath_temperature,
            outdoor_bath_rating=args.outdoor_bath_rating,
            pre_visit_mood=args.pre_visit_mood,
            post_visit_mood=args.post_visit_mood,
            energy_level_change=args.energy_level_change,
            hydration_level=args.hydration_level,
            previous_location=args.previous_location,
            next_location=args.next_location,
            multi_onsen_day=args.multi_onsen_day,
            visit_order=args.visit_order,
            atmosphere_rating=args.atmosphere_rating,
            personal_rating=args.personal_rating,
        )
        db.add(visit)
        db.commit()
        logger.info(f"Added a visit to onsen {onsen.name} (id={onsen.id})")


def main():
    parser = argparse.ArgumentParser(description="Onsen CLI")
    subparsers = parser.add_subparsers(help="Sub-commands")

    # Sub-command: add_onsen
    parser_add_onsen = subparsers.add_parser("add-onsen", help="Add a new onsen.")
    parser_add_onsen.add_argument("--ban_number", required=True)
    parser_add_onsen.add_argument("--name", required=True)
    parser_add_onsen.add_argument("--address", default="")
    # ... add more fields as necessary
    parser_add_onsen.set_defaults(func=add_onsen)

    # Sub-command: add_visit
    parser_add_visit = subparsers.add_parser("add-visit", help="Add a new onsen visit.")
    parser_add_visit.add_argument("--onsen_id", type=int, required=True)
    parser_add_visit.add_argument("--entry_fee_yen", type=int, default=0)
    parser_add_visit.add_argument("--payment_method", type=str, default="")
    parser_add_visit.add_argument("--weather", type=str, default="")
    parser_add_visit.add_argument("--time_of_day", type=str, default="")
    parser_add_visit.add_argument(
        "--temperature_outside_celsius", type=float, default=0
    )
    parser_add_visit.add_argument("--visit_time", help="YYYY-MM-DD HH:MM", default=None)
    parser_add_visit.add_argument("--stay_length_minutes", type=int, default=0)
    parser_add_visit.add_argument("--visited_with", type=str, default="")
    parser_add_visit.add_argument("--travel_mode", type=str, default="")
    parser_add_visit.add_argument("--travel_time_minutes", type=int, default=0)
    parser_add_visit.add_argument("--accessibility_rating", type=int, default=0)
    parser_add_visit.add_argument("--excercise_before_onsen", action="store_true")
    parser_add_visit.add_argument("--excercise_type", type=str, default="")
    parser_add_visit.add_argument("--excercise_length_minutes", type=int, default=0)
    parser_add_visit.add_argument("--crowd_level", type=str, default="")
    parser_add_visit.add_argument("--heart_rate_data", type=str, default="")
    parser_add_visit.add_argument("--cleanliness_rating", type=int, default=0)
    parser_add_visit.add_argument("--navigability_rating", type=int, default=0)
    parser_add_visit.add_argument("--view_rating", type=int, default=0)
    parser_add_visit.add_argument("--main_bath_type", type=str, default="")
    parser_add_visit.add_argument("--main_bath_temperature", type=int, default=0)
    parser_add_visit.add_argument("--main_bath_water_type", type=str, default="")
    parser_add_visit.add_argument("--water_color", type=str, default="")
    parser_add_visit.add_argument("--smell_intensity_rating", type=int, default=0)
    parser_add_visit.add_argument(
        "--changing_room_cleanliness_rating", type=int, default=0
    )
    parser_add_visit.add_argument("--locker_availability_rating", type=int, default=0)
    parser_add_visit.add_argument("--had_soap", action="store_true")
    parser_add_visit.add_argument("--had_sauna", action="store_true")
    parser_add_visit.add_argument("--had_outdoor_bath", action="store_true")
    parser_add_visit.add_argument("--had_rest_area", action="store_true")
    parser_add_visit.add_argument("--had_food_service", action="store_true")
    parser_add_visit.add_argument("--rest_area_rating", type=int, default=0)
    parser_add_visit.add_argument("--food_quality_rating", type=int, default=0)
    parser_add_visit.add_argument("--massage_chair_available", action="store_true")
    parser_add_visit.add_argument("--sauna_visited", action="store_true")
    parser_add_visit.add_argument("--sauna_temperature", type=int, default=0)
    parser_add_visit.add_argument("--sauna_steam", action="store_true")
    parser_add_visit.add_argument("--sauna_duration_minutes", type=int, default=0)
    parser_add_visit.add_argument("--sauna_rating", type=int, default=0)
    parser_add_visit.add_argument("--outdoor_bath_visited", action="store_true")
    parser_add_visit.add_argument("--outdoor_bath_temperature", type=int, default=0)
    parser_add_visit.add_argument("--outdoor_bath_rating", type=int, default=0)
    parser_add_visit.add_argument("--pre_visit_mood", type=str, default="")
    parser_add_visit.add_argument("--post_visit_mood", type=str, default="")
    parser_add_visit.add_argument("--energy_level_change", type=int, default=0)
    parser_add_visit.add_argument("--hydration_level", type=int, default=0)
    parser_add_visit.add_argument("--previous_location", type=int, default=0)
    parser_add_visit.add_argument("--next_location", type=int, default=0)
    parser_add_visit.add_argument("--multi_onsen_day", action="store_true")
    parser_add_visit.add_argument("--visit_order", type=int, default=0)
    parser_add_visit.add_argument("--atmosphere_rating", type=int, default=0)
    parser_add_visit.add_argument("--personal_rating", type=int, default=0)

    parser_add_visit.set_defaults(func=add_visit)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
