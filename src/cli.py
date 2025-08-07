"""
cli.py

A simple CLI to demonstrate how you might add or update onsen data
or add onsen visits. You could use argparse or click for a nicer interface.
"""

import argparse
from loguru import logger
from src import config
from src.db.conn import SessionLocal
from src.db.models import Onsen, OnsenVisit


def add_onsen(args):
    with SessionLocal() as db:
        args_dict = vars(args)
        args_dict.pop("func", None)

        onsen = Onsen(**args_dict)
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


COMMANDS = {
    "add-onsen": {
        "args": {
            "ban_number": {"type": str, "required": True},
            "name": {"type": str, "required": True},
            "address": {"type": str, "default": ""},
        },
        "func": add_onsen,
    },
    "add-visit": {
        "func": add_visit,
        "args": {
            # Required fields
            "onsen_id": {"type": int, "required": True},
            # Integer fields
            "entry_fee_yen": {"type": int, "default": 0},
            "stay_length_minutes": {"type": int, "default": 0},
            "travel_time_minutes": {"type": int, "default": 0},
            "accessibility_rating": {"type": int, "default": 0},
            "excercise_length_minutes": {"type": int, "default": 0},
            "cleanliness_rating": {"type": int, "default": 0},
            "navigability_rating": {"type": int, "default": 0},
            "view_rating": {"type": int, "default": 0},
            "main_bath_temperature": {"type": int, "default": 0},
            "smell_intensity_rating": {"type": int, "default": 0},
            "changing_room_cleanliness_rating": {"type": int, "default": 0},
            "locker_availability_rating": {"type": int, "default": 0},
            "rest_area_rating": {"type": int, "default": 0},
            "food_quality_rating": {"type": int, "default": 0},
            "sauna_temperature": {"type": int, "default": 0},
            "sauna_duration_minutes": {"type": int, "default": 0},
            "sauna_rating": {"type": int, "default": 0},
            "outdoor_bath_temperature": {"type": int, "default": 0},
            "outdoor_bath_rating": {"type": int, "default": 0},
            "energy_level_change": {"type": int, "default": 0},
            "hydration_level": {"type": int, "default": 0},
            "previous_location": {"type": int, "default": 0},
            "next_location": {"type": int, "default": 0},
            "visit_order": {"type": int, "default": 0},
            "atmosphere_rating": {"type": int, "default": 0},
            "personal_rating": {"type": int, "default": 0},
            # Float fields
            "temperature_outside_celsius": {"type": float, "default": 0},
            # String fields with defaults
            "payment_method": {"type": str, "default": ""},
            "weather": {"type": str, "default": ""},
            "time_of_day": {"type": str, "default": ""},
            "visited_with": {"type": str, "default": ""},
            "travel_mode": {"type": str, "default": ""},
            "excercise_type": {"type": str, "default": ""},
            "crowd_level": {"type": str, "default": ""},
            "heart_rate_data": {"type": str, "default": ""},
            "main_bath_type": {"type": str, "default": ""},
            "main_bath_water_type": {"type": str, "default": ""},
            "water_color": {"type": str, "default": ""},
            "pre_visit_mood": {"type": str, "default": ""},
            "post_visit_mood": {"type": str, "default": ""},
            # Special fields
            "visit_time": {"help": "YYYY-MM-DD HH:MM", "default": None},
            # Boolean fields
            "excercise_before_onsen": {"action": "store_true"},
            "had_soap": {"action": "store_true"},
            "had_sauna": {"action": "store_true"},
            "had_outdoor_bath": {"action": "store_true"},
            "had_rest_area": {"action": "store_true"},
            "had_food_service": {"action": "store_true"},
            "massage_chair_available": {"action": "store_true"},
            "sauna_visited": {"action": "store_true"},
            "sauna_steam": {"action": "store_true"},
            "outdoor_bath_visited": {"action": "store_true"},
            "multi_onsen_day": {"action": "store_true"},
        },
    },
}


def main():
    parser = argparse.ArgumentParser(description=f"{config.CLI_NAME}")
    subparsers = parser.add_subparsers(help="Sub-commands")

    for command, config in COMMANDS.items():
        parser_command = subparsers.add_parser(command, help=config["help"])
        for arg, kwargs in config["args"].items():
            parser_command.add_argument(arg, **kwargs)
        parser_command.set_defaults(func=config["func"])

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
