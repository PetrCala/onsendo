"""
Data mapper for converting scraped onsen data to database model format.
"""

from typing import Any, Optional


def map_scraped_data_to_onsen_model(scraped_data: dict[str, Any]) -> dict[str, Any]:
    """
    Map scraped onsen data to the Onsen model fields.

    Args:
        scraped_data: Raw scraped data from the onsen page

    Returns:
        Dict with mapped data ready for database insertion
    """
    mapped_data = {}

    # Basic fields
    mapped_data["region"] = scraped_data.get("region", "")
    mapped_data["ban_number"] = scraped_data.get("ban_number", "")
    mapped_data["name"] = scraped_data.get("name", "")
    mapped_data["deleted"] = scraped_data.get("deleted", False)

    # Coordinates
    mapped_data["latitude"] = scraped_data.get("latitude")
    mapped_data["longitude"] = scraped_data.get("longitude")

    # Map table data to model fields
    table_data = scraped_data

    # Direct mappings from table data
    field_mappings = {
        "住所": "address",
        "電話": "phone",
        "入浴料金": "admission_fee",
        "利用時間": "usage_time",
        "定休日ほか": "closed_days",
        "家族湯(貸切湯)": "private_bath",
        "泉質": "spring_quality",
        "最寄バス停": "nearest_bus_stop",
        "最寄駅(徒歩)": "nearest_station",
        "駐車場": "parking",
        "備考": "remarks",
        "営業形態": "business_form",
    }

    for japanese_key, english_field in field_mappings.items():
        if japanese_key in table_data:
            mapped_data[english_field] = table_data[japanese_key]
        else:
            mapped_data[english_field] = None

    # Create description from available data
    mapped_data["description"] = create_description(scraped_data)

    return mapped_data


def create_description(scraped_data: dict[str, Any]) -> str:
    """
    Create a description from available scraped data.

    Args:
        scraped_data: Raw scraped data

    Returns:
        Formatted description string
    """
    description_parts = []

    # Add name if available
    if scraped_data.get("name"):
        description_parts.append(f"温泉名: {scraped_data['name']}")

    # Add spring quality if available
    if scraped_data.get("泉質"):
        description_parts.append(f"泉質: {scraped_data['泉質']}")

    # Add business form if available
    if scraped_data.get("営業形態"):
        description_parts.append(f"営業形態: {scraped_data['営業形態']}")

    # Add admission fee if available
    if scraped_data.get("入浴料金"):
        description_parts.append(f"入浴料金: {scraped_data['入浴料金']}")

    # Add usage time if available
    if scraped_data.get("利用時間"):
        description_parts.append(f"利用時間: {scraped_data['利用時間']}")

    # Add remarks if available
    if scraped_data.get("備考"):
        description_parts.append(f"備考: {scraped_data['備考']}")

    return " | ".join(description_parts) if description_parts else ""


def validate_mapped_data(mapped_data: dict[str, Any]) -> bool:
    """
    Validate that mapped data has required fields.

    Args:
        mapped_data: Mapped data dictionary

    Returns:
        True if data is valid, False otherwise
    """
    required_fields = ["region", "name", "ban_number"]

    for field in required_fields:
        if not mapped_data.get(field):
            return False

    return True


def get_mapping_summary(scraped_data: dict[str, Any]) -> dict[str, Any]:
    """
    Get a summary of the mapping process.

    Args:
        scraped_data: Raw scraped data

    Returns:
        Summary dictionary
    """
    mapped_data = map_scraped_data_to_onsen_model(scraped_data)

    summary = {
        "total_fields": len(mapped_data),
        "filled_fields": sum(
            1 for v in mapped_data.values() if v is not None and v != ""
        ),
        "required_fields_present": validate_mapped_data(mapped_data),
        "has_coordinates": mapped_data.get("latitude") is not None
        and mapped_data.get("longitude") is not None,
        "table_entries_mapped": len(
            [
                k
                for k in mapped_data.keys()
                if k
                in [
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
                    "business_form",
                ]
                and mapped_data[k] is not None
            ]
        ),
    }

    return summary
