import json
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session
from src.db.models import Onsen


def import_onsen_data(db: Session, json_path: str) -> dict[str, int]:  # pylint: disable=too-complex
    """
    Import onsens from a scraped JSON file and upsert into the database.

    Note: This function has intentional complexity due to multiple validation checks,
    error handling paths, and data transformation logic for importing onsen data.

    The JSON is produced by the individual onsen scraping pipeline and has the form:
    ```json
    {
      "<onsen_id>": {
        "onsen_id": "<onsen_id>",
        ...,
        "mapped_data": { <fields matching Onsen columns> },
        ...
      },
      ...
    }
    ```

    Returns a summary dict with counts for inserted and updated rows.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # Broad exception needed for file I/O and JSON parsing errors
        logger.error(f"Failed to read JSON from {json_path}: {exc}")
        return {"inserted": 0, "updated": 0, "skipped": 0}

    inserted = 0
    updated = 0
    skipped = 0

    # Columns present in the Onsen model and supported by mapped_data
    onsen_fields = [
        "ban_number",
        "name",
        "region",
        "latitude",
        "longitude",
        "description",
        "business_form",
        "address",
        "phone",
        "admission_fee",
        "usage_time",
        "closed_days",
        "private_bath",
        "spring_quality",
        "nearest_bus_stop",
        "nearest_station",
        "parking",
        "remarks",
    ]

    for onsen_id_str, payload in data.items():
        try:
            onsen_id = int(onsen_id_str)
        except Exception:  # pylint: disable=broad-exception-caught
            # Broad exception needed for type conversion errors
            logger.warning(f"Skipping entry with non-integer key: {onsen_id_str}")
            skipped += 1
            continue

        mapped: dict[str, Any] = payload.get("mapped_data") or {}

        # Basic validation of required fields
        if (
            not mapped.get("ban_number")
            or not mapped.get("name")
            or not mapped.get("region")
        ):
            logger.warning(
                f"Skipping onsen_id={onsen_id}: missing required fields in mapped_data"
            )
            skipped += 1
            continue

        # Build values for the Onsen model
        values: dict[str, Any] = {field: mapped.get(field) for field in onsen_fields}

        existing = db.query(Onsen).filter(Onsen.id == onsen_id).first()
        if existing:
            for key, val in values.items():
                setattr(existing, key, val)
            updated += 1
        else:
            # Try to find by unique ban_number if id not found
            existing_by_ban = (
                db.query(Onsen).filter(Onsen.ban_number == values["ban_number"]).first()
            )
            if existing_by_ban:
                # Update fields and attempt to set the id to the scraped id
                for key, val in values.items():
                    setattr(existing_by_ban, key, val)
                try:
                    existing_by_ban.id = onsen_id
                    updated += 1
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    # Broad exception needed for database constraint errors
                    logger.warning(
                        f"Could not update primary key for ban={values['ban_number']} to id={onsen_id}: {exc}"
                    )
                    updated += 1
            else:
                new_onsen = Onsen(id=onsen_id, **values)
                db.add(new_onsen)
                inserted += 1

    db.commit()

    summary = {"inserted": inserted, "updated": updated, "skipped": skipped}
    logger.info(
        f"Onsen import from JSON complete. Inserted: {inserted}, Updated: {updated}, Skipped: {skipped}"
    )
    return summary
