"""
Example script demonstrating the data mapping functionality.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from src.cli.commands.onsen.scrape_data.data_mapper import (
    map_scraped_data_to_onsen_model,
    get_mapping_summary,
)


def demonstrate_mapping():
    """Demonstrate the data mapping functionality with sample data."""

    # Sample scraped data (what would be extracted from a real onsen page)
    sample_scraped_data = {
        "region": "別府",
        "ban_number": "123",
        "name": "別府温泉 海地獄",
        "latitude": 33.2797,
        "longitude": 131.5011,
        "map_url": "https://maps.google.co.jp/maps?q=33.2797,131.5011&z=15",
        "住所": "大分県別府市鉄輪559-1",
        "電話": "0977-66-1577",
        "営業形態": "日帰り入浴",
        "入浴料金": "大人400円、小人200円",
        "利用時間": "8:30～17:00（年中無休）",
        "定休日ほか": "年中無休",
        "家族湯(貸切湯)": "あり（要予約）",
        "泉質": "含硫黄-ナトリウム-塩化物泉",
        "最寄バス停": "海地獄前（徒歩1分）",
        "最寄駅(徒歩)": "別府駅（バス15分）",
        "駐車場": "あり（無料）",
        "備考": "観光地としても人気の温泉施設",
    }

    print("Sample Scraped Data:")
    print("=" * 50)
    for key, value in sample_scraped_data.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 50)
    print("MAPPING TO DATABASE FORMAT")
    print("=" * 50)

    # Map the data to database format
    mapped_data = map_scraped_data_to_onsen_model(sample_scraped_data)

    print("Mapped Data (ready for database insertion):")
    print("-" * 50)
    for key, value in mapped_data.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 50)
    print("MAPPING SUMMARY")
    print("=" * 50)

    # Get mapping summary
    summary = get_mapping_summary(sample_scraped_data)

    print(f"Total fields: {summary['total_fields']}")
    print(f"Filled fields: {summary['filled_fields']}")
    print(f"Required fields present: {summary['required_fields_present']}")
    print(f"Has coordinates: {summary['has_coordinates']}")
    print(f"Table entries mapped: {summary['table_entries_mapped']}")

    print("\n" + "=" * 50)
    print("DATABASE MODEL FIELDS")
    print("=" * 50)

    # Show which database model fields are populated
    model_fields = [
        "name",
        "ban_number",
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

    for field in model_fields:
        value = mapped_data.get(field)
        status = "✓" if value else "✗"
        print(f"{status} {field}: {value}")


def show_field_mappings():
    """Show the Japanese to English field mappings."""

    print("\n" + "=" * 50)
    print("JAPANESE TO ENGLISH FIELD MAPPINGS")
    print("=" * 50)

    mappings = {
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

    for japanese, english in mappings.items():
        print(f"{japanese} → {english}")


if __name__ == "__main__":
    print("ONSEN DATA MAPPING DEMONSTRATION")
    print("=" * 50)

    demonstrate_mapping()
    show_field_mappings()

    print("\n" + "=" * 50)
    print("This demonstrates how scraped Japanese onsen data is automatically")
    print("mapped to English database model fields for easy integration.")
    print("=" * 50)
