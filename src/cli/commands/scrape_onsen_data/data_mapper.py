"""
Data mapper for converting scraped onsen data to database model format.
"""

from typing import Dict, Any, Optional


def map_scraped_data_to_onsen_model(scraped_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map scraped onsen data to the Onsen model fields.

    Args:
        scraped_data: Raw scraped data from the onsen page

    Returns:
        Dict with mapped data ready for database insertion
    """
    mapped_data = {}

    # Basic fields
    mapped_data["name"] = scraped_data.get("name", "")

    # Extract ban number from the combined field
    ban_number_and_name = scraped_data.get("ban_number_and_name", "")
    mapped_data["ban_number"] = extract_ban_number(ban_number_and_name)

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

    # Extract region from address or name if available
    mapped_data["region"] = extract_region(
        mapped_data.get("address", ""), mapped_data.get("name", "")
    )

    # Create description from available data
    mapped_data["description"] = create_description(scraped_data)

    return mapped_data


def extract_ban_number(ban_number_and_name: str) -> str:
    """
    Extract ban number from the combined ban number and name field.

    Args:
        ban_number_and_name: String containing ban number and name

    Returns:
        Extracted ban number
    """
    if not ban_number_and_name:
        return ""

    # Try to extract ban number (usually at the beginning, before the name)
    # Common patterns: "番号: 123 温泉名" or "123 温泉名"
    import re

    # Look for numbers at the beginning
    match = re.match(r"^(\d+)", ban_number_and_name.strip())
    if match:
        return match.group(1)

    # Look for "番号:" pattern
    match = re.search(r"番号[:\s]*(\d+)", ban_number_and_name)
    if match:
        return match.group(1)

    # If no clear pattern, return the whole string
    return ban_number_and_name.strip()


def extract_region(address: str, name: str) -> Optional[str]:
    """
    Extract region information from address or name.

    Args:
        address: Full address string
        name: Onsen name

    Returns:
        Extracted region or None
    """
    if not address and not name:
        return None

    # Common regions in Oita prefecture
    regions = [
        "別府",
        "Beppu",
        "湯布院",
        "Yufuin",
        "由布院",
        "大分",
        "Oita",
        "日田",
        "Hita",
        "中津",
        "Nakatsu",
        "佐伯",
        "Saiki",
        "臼杵",
        "Usuki",
    ]

    # Check address first
    if address:
        for region in regions:
            if region in address:
                return region

    # Check name if no region found in address
    if name:
        for region in regions:
            if region in name:
                return region

    return None


def create_description(scraped_data: Dict[str, Any]) -> str:
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


def validate_mapped_data(mapped_data: Dict[str, Any]) -> bool:
    """
    Validate that mapped data has required fields.

    Args:
        mapped_data: Mapped data dictionary

    Returns:
        True if data is valid, False otherwise
    """
    required_fields = ["name", "ban_number"]

    for field in required_fields:
        if not mapped_data.get(field):
            return False

    return True


def get_mapping_summary(scraped_data: Dict[str, Any]) -> Dict[str, Any]:
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
