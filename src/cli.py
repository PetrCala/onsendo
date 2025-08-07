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

        args_dict = vars(args)
        args_dict.pop("onsen_id", None)
        args_dict.pop("func", None)  # Not a model field

        # Create the visit with dynamic arguments
        visit = OnsenVisit(onsen_id=onsen.id, **args_dict)
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
