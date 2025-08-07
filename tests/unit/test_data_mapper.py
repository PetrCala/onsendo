"""
Unit tests for the data mapper functionality.
"""

import pytest
from unittest.mock import patch

from src.cli.commands.scrape_onsen_data.data_mapper import (
    map_scraped_data_to_onsen_model,
    extract_ban_number,
    extract_region,
    create_description,
    validate_mapped_data,
    get_mapping_summary,
)
from src.testing.mocks.mock_onsen_data import (
    get_mock_extracted_data,
    get_mock_mapped_data,
    get_mock_incomplete_data,
    get_mock_yufuin_data,
)


class TestDataMapper:
    """Test cases for data mapper functionality."""

    def test_map_scraped_data_to_onsen_model_complete(
        self, mock_extracted_data, mock_mapped_data
    ):
        """Test mapping complete scraped data to onsen model."""
        result = map_scraped_data_to_onsen_model(mock_extracted_data)

        # Check basic fields
        assert result["name"] == "別府温泉 海地獄"
        assert result["ban_number"] == "123"
        assert result["region"] == "別府"
        assert result["latitude"] == 33.2797
        assert result["longitude"] == 131.5011

        # Check mapped table fields
        assert result["address"] == "大分県別府市鉄輪559-1"
        assert result["phone"] == "0977-66-1577"
        assert result["business_form"] == "日帰り入浴"
        assert result["admission_fee"] == "大人400円、小人200円"
        assert result["spring_quality"] == "含硫黄-ナトリウム-塩化物泉"

        # Check description creation
        assert "温泉名: 別府温泉 海地獄" in result["description"]
        assert "泉質: 含硫黄-ナトリウム-塩化物泉" in result["description"]

    def test_map_scraped_data_to_onsen_model_incomplete(self):
        """Test mapping incomplete scraped data."""
        incomplete_data = get_mock_incomplete_data()
        result = map_scraped_data_to_onsen_model(incomplete_data)

        # Check that available fields are mapped
        assert result["name"] == "テスト温泉"
        assert result["ban_number"] == "456"
        assert result["region"] == "大分"
        assert result["address"] == "大分県大分市テスト町1-1"
        assert result["phone"] == "097-123-4567"

        # Check that missing fields are None
        assert result["latitude"] is None
        assert result["longitude"] is None
        assert result["admission_fee"] is None
        assert result["spring_quality"] is None

    def test_extract_ban_number_simple(self):
        """Test extracting ban number from simple format."""
        result = extract_ban_number("123 温泉名")
        assert result == "123"

    def test_extract_ban_number_with_label(self):
        """Test extracting ban number with label."""
        result = extract_ban_number("番号: 456 温泉名")
        assert result == "456"

    def test_extract_ban_number_with_spaces(self):
        """Test extracting ban number with spaces."""
        result = extract_ban_number("番号 : 789 温泉名")
        assert result == "789"

    def test_extract_ban_number_no_number(self):
        """Test extracting ban number when no number is present."""
        result = extract_ban_number("温泉名のみ")
        assert result == "温泉名のみ"

    def test_extract_ban_number_empty(self):
        """Test extracting ban number from empty string."""
        result = extract_ban_number("")
        assert result == ""

    def test_extract_region_from_address(self):
        """Test extracting region from address."""
        result = extract_region("大分県別府市鉄輪559-1", "温泉名")
        assert result == "別府"

    def test_extract_region_from_name(self):
        """Test extracting region from name when not in address."""
        result = extract_region("大分県大分市テスト町1-1", "湯布院温泉")
        assert result == "湯布院"

    def test_extract_region_not_found(self):
        """Test extracting region when not found."""
        result = extract_region("大分県テスト市テスト町1-1", "テスト温泉")
        assert result is None

    def test_extract_region_empty_inputs(self):
        """Test extracting region with empty inputs."""
        result = extract_region("", "")
        assert result is None

    def test_create_description_with_all_fields(self, mock_extracted_data):
        """Test creating description with all available fields."""
        result = create_description(mock_extracted_data)

        assert "温泉名: 別府温泉 海地獄" in result
        assert "泉質: 含硫黄-ナトリウム-塩化物泉" in result
        assert "営業形態: 日帰り入浴" in result
        assert "入浴料金: 大人400円、小人200円" in result
        assert "利用時間: 8:30～17:00（年中無休）" in result
        assert "備考: 観光地としても人気の温泉施設" in result

    def test_create_description_with_minimal_fields(self):
        """Test creating description with minimal fields."""
        minimal_data = {"name": "テスト温泉"}
        result = create_description(minimal_data)

        assert result == "温泉名: テスト温泉"

    def test_create_description_empty(self):
        """Test creating description with no fields."""
        result = create_description({})
        assert result == ""

    def test_validate_mapped_data_valid(self, mock_mapped_data):
        """Test validation of valid mapped data."""
        assert validate_mapped_data(mock_mapped_data) is True

    def test_validate_mapped_data_missing_name(self):
        """Test validation of mapped data missing name."""
        invalid_data = {"ban_number": "123"}
        assert validate_mapped_data(invalid_data) is False

    def test_validate_mapped_data_missing_ban_number(self):
        """Test validation of mapped data missing ban number."""
        invalid_data = {"name": "温泉名"}
        assert validate_mapped_data(invalid_data) is False

    def test_validate_mapped_data_empty_fields(self):
        """Test validation of mapped data with empty required fields."""
        invalid_data = {"name": "", "ban_number": ""}
        assert validate_mapped_data(invalid_data) is False

    def test_get_mapping_summary_complete(self, mock_extracted_data):
        """Test getting mapping summary for complete data."""
        summary = get_mapping_summary(mock_extracted_data)

        assert summary["total_fields"] == 18
        assert summary["filled_fields"] == 18
        assert summary["required_fields_present"] is True
        assert summary["has_coordinates"] is True
        assert summary["table_entries_mapped"] == 12

    def test_get_mapping_summary_incomplete(self):
        """Test getting mapping summary for incomplete data."""
        incomplete_data = get_mock_incomplete_data()
        summary = get_mapping_summary(incomplete_data)

        assert summary["total_fields"] == 18
        assert summary["filled_fields"] < 18  # Some fields are missing
        assert summary["required_fields_present"] is True
        assert summary["has_coordinates"] is False
        assert summary["table_entries_mapped"] < 12  # Fewer table entries

    def test_get_mapping_summary_invalid(self):
        """Test getting mapping summary for invalid data."""
        invalid_data = {"name": "", "ban_number": ""}
        summary = get_mapping_summary(invalid_data)

        assert summary["required_fields_present"] is False
        assert summary["has_coordinates"] is False
        assert summary["table_entries_mapped"] == 0

    def test_mapping_with_different_regions(self):
        """Test mapping data from different regions."""
        yufuin_data = get_mock_yufuin_data()
        result = map_scraped_data_to_onsen_model(yufuin_data)

        assert result["name"] == "湯布院温泉 金鱗湖"
        assert result["ban_number"] == "789"
        assert result["region"] == "湯布院"
        assert result["latitude"] == 33.2633
        assert result["longitude"] == 131.3544
        assert result["address"] == "大分県由布市湯布院町川上"

    def test_mapping_field_mappings(self, mock_extracted_data):
        """Test that all Japanese field mappings work correctly."""
        result = map_scraped_data_to_onsen_model(mock_extracted_data)

        # Test all field mappings
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
            japanese_value = mock_extracted_data.get(japanese_key)
            english_value = result.get(english_field)
            assert (
                english_value == japanese_value
            ), f"Mapping failed for {japanese_key} -> {english_field}"

    def test_mapping_with_none_values(self):
        """Test mapping with None values in the data."""
        data_with_nones = {
            "name": "テスト温泉",
            "ban_number_and_name": "123 テスト温泉",
            "latitude": None,
            "longitude": None,
            "住所": None,
            "電話": None,
        }

        result = map_scraped_data_to_onsen_model(data_with_nones)

        assert result["name"] == "テスト温泉"
        assert result["ban_number"] == "123"
        assert result["latitude"] is None
        assert result["longitude"] is None
        assert result["address"] is None
        assert result["phone"] is None
