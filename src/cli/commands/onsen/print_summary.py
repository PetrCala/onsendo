"""
print_onsen_summary.py

Print a summary of an onsen specified by its ID, BAN number, or name.
"""

import argparse
from datetime import datetime
from typing import Optional

from loguru import logger

from src.db.conn import get_db_from_args
from src.db.models import Onsen, OnsenVisit
from src.lib.utils import generate_google_maps_link


def _format_datetime(dt: Optional[datetime]) -> str:
    if not dt:
        return "N/A"
    try:
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(dt)


def print_summary(args: argparse.Namespace) -> None:
    """
    Print a human-readable summary for an onsen.

    One (and only one) of --onsen_id, --ban_number, or --name should be provided.
    """
    onsen_id: Optional[int] = getattr(args, "onsen_id", None)
    ban_number: Optional[str] = getattr(args, "ban_number", None)
    name: Optional[str] = getattr(args, "name", None)

    provided = [v for v in [onsen_id, ban_number, name] if v]
    if not provided:
        logger.error("You must provide one of --onsen-id, --ban-number, or --name")
        return

    if len(provided) > 1:
        logger.warning(
            "Multiple identifiers provided. Using priority: id > ban > name."
        )

    # Get database configuration
    config = get_database_config(
        env_override=getattr(args, "env", None),
        path_override=getattr(args, "database", None),
    )

    with get_db(url=config.url) as db:
        query = db.query(Onsen)
        if onsen_id:
            onsen = query.filter(Onsen.id == onsen_id).first()
        elif ban_number:
            onsen = query.filter(Onsen.ban_number == ban_number).first()
        else:
            matches = query.filter(Onsen.name == name).order_by(Onsen.id.asc()).all()
            if not matches:
                logger.error(f"Onsen not found for name={name}")
                return
            if len(matches) > 1:
                logger.warning(
                    "Multiple onsens matched the provided name. "
                    f"Using id={matches[0].id} (BAN {matches[0].ban_number})."
                )
            onsen = matches[0]

        if not onsen:
            identifier = (
                f"id={onsen_id}"
                if onsen_id
                else (f"ban_number={ban_number}" if ban_number else f"name={name}")
            )
            logger.error(f"Onsen not found for {identifier}")
            return

        # Fetch visits and some simple aggregates
        visits = db.query(OnsenVisit).filter(OnsenVisit.onsen_id == onsen.id).all()
        visit_count = len(visits)
        last_visit_time: Optional[datetime] = None
        if visit_count:
            last_visit_time = max(
                (v.visit_time for v in visits if v.visit_time), default=None
            )

        def average(values: list[Optional[int | float]]) -> Optional[float]:
            numeric = [v for v in values if isinstance(v, (int, float))]
            if not numeric:
                return None
            return sum(numeric) / len(numeric)

        avg_personal = average([v.personal_rating for v in visits])
        avg_clean = average([v.cleanliness_rating for v in visits])
        avg_atmos = average([v.atmosphere_rating for v in visits])

        # Print summary
        print("\n" + "=" * 50)
        print("ONSEN SUMMARY")
        print("=" * 50)

        print(f"Name           : {onsen.name}")
        print(f"ID / BAN       : {onsen.id} / {onsen.ban_number}")
        if onsen.region:
            print(f"Region         : {onsen.region}")
        print(
            "Coordinates    : "
            + (
                f"{onsen.latitude}, {onsen.longitude}"
                if onsen.latitude is not None and onsen.longitude is not None
                else "N/A"
            )
        )
        if onsen.address:
            print(f"Address        : {onsen.address}")
        if (link := generate_google_maps_link(onsen)) != "N/A":
            print(f"Google Maps    : {link}")
        if onsen.phone:
            print(f"Phone          : {onsen.phone}")
        if onsen.business_form:
            print(f"Business form  : {onsen.business_form}")
        if onsen.admission_fee:
            print(f"Admission fee  : {onsen.admission_fee}")
        if onsen.usage_time:
            print(f"Usage time     : {onsen.usage_time}")
        if onsen.closed_days:
            print(f"Closed days    : {onsen.closed_days}")
        if onsen.spring_quality:
            print(f"Spring quality : {onsen.spring_quality}")
        if onsen.private_bath:
            print(f"Private bath   : {onsen.private_bath}")
        if onsen.nearest_bus_stop:
            print(f"Nearest bus    : {onsen.nearest_bus_stop}")
        if onsen.nearest_station:
            print(f"Nearest station: {onsen.nearest_station}")
        if onsen.parking:
            print(f"Parking        : {onsen.parking}")
        if onsen.remarks:
            print(f"Remarks        : {onsen.remarks}")

        print("-" * 50)
        print(f"Visits         : {visit_count}")
        print(f"Last visit     : {_format_datetime(last_visit_time)}")
        if avg_personal is not None:
            print(f"Avg personal   : {avg_personal:.1f} / 10")
        if avg_clean is not None:
            print(f"Avg cleanliness: {avg_clean:.1f} / 10")
        if avg_atmos is not None:
            print(f"Avg atmosphere : {avg_atmos:.1f} / 10")
        print("=" * 50)
