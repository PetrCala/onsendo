"""
Basic test for the onsen scraper module structure.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")

    try:
        from src.cli.commands.scrape_onsen_data import scrape_onsen_data
        from src.cli.commands.scrape_onsen_data.scraper import (
            setup_selenium_driver,
            extract_all_onsen_mapping,
            scrape_onsen_page_with_selenium,
        )
        from src.cli.commands.scrape_onsen_data.data_mapper import (
            map_scraped_data_to_onsen_model,
            get_mapping_summary,
        )

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_paths():
    """Test that paths are correctly defined."""
    print("Testing paths...")

    try:
        from src.paths import PATHS

        # Check that output paths are defined
        assert hasattr(PATHS, "OUTPUT_DIR")
        assert hasattr(PATHS, "SCRAPED_ONSEN_DATA_FILE")
        assert hasattr(PATHS, "ONSEN_MAPPING_FILE")

        print("✓ All paths correctly defined")
        return True
    except Exception as e:
        print(f"✗ Path error: {e}")
        return False


def test_constants():
    """Test that constants are correctly defined."""
    print("Testing constants...")

    try:
        from src.const import CONST

        # Check that onsen URLs are defined
        assert hasattr(CONST, "ONSEN_URL")
        assert hasattr(CONST, "ONSEN_DETAIL_URL_TEMPLATE")

        print("✓ All constants correctly defined")
        return True
    except Exception as e:
        print(f"✗ Constant error: {e}")
        return False


def test_file_structure():
    """Test that all required files exist."""
    print("Testing file structure...")

    required_files = [
        "__init__.py",
        "scraper.py",
        "test_scraper.py",
        "README.md",
        "data_mapper.py",
    ]

    current_dir = os.path.dirname(__file__)

    for file_name in required_files:
        file_path = os.path.join(current_dir, file_name)
        if os.path.exists(file_path):
            print(f"✓ {file_name} exists")
        else:
            print(f"✗ {file_name} missing")
            return False

    return True


def test_data_mapper():
    """Test the data mapper functionality."""
    print("Testing data mapper...")

    try:
        from src.cli.commands.scrape_onsen_data.data_mapper import (
            map_scraped_data_to_onsen_model,
            get_mapping_summary,
        )

        # Test with sample data
        sample_data = {
            "name": "テスト温泉",
            "ban_number_and_name": "123 テスト温泉",
            "latitude": 33.123,
            "longitude": 131.456,
            "住所": "大分県別府市テスト町1-1",
            "電話": "0977-12-3456",
            "入浴料金": "500円",
        }

        mapped_data = map_scraped_data_to_onsen_model(sample_data)
        summary = get_mapping_summary(sample_data)

        # Check that mapping worked
        assert "name" in mapped_data
        assert "ban_number" in mapped_data
        assert "address" in mapped_data
        assert "phone" in mapped_data

        print("✓ Data mapper functionality works")
        return True

    except Exception as e:
        print(f"✗ Data mapper error: {e}")
        return False


def test_mock_data():
    """Test that mock data is available and properly structured."""
    print("Testing mock data...")

    try:
        from src.testing.mocks.mock_onsen_data import (
            get_mock_onsen_mapping,
            get_mock_extracted_data,
            get_mock_mapped_data,
            get_mock_complete_entry,
        )

        # Test mock data functions
        mapping = get_mock_onsen_mapping()
        extracted = get_mock_extracted_data()
        mapped = get_mock_mapped_data()
        complete = get_mock_complete_entry()

        # Check that data is properly structured
        assert isinstance(mapping, dict)
        assert isinstance(extracted, dict)
        assert isinstance(mapped, dict)
        assert isinstance(complete, dict)

        print("✓ Mock data is available and properly structured")
        return True

    except Exception as e:
        print(f"✗ Mock data error: {e}")
        return False


def test_fixtures():
    """Test that test fixtures are available."""
    print("Testing fixtures...")

    try:
        from src.testing.testutils.scraper_fixtures import (
            temp_output_dir,
            mock_selenium_driver,
            mock_onsen_mapping,
            mock_extracted_data,
        )

        print("✓ Test fixtures are available")
        return True

    except Exception as e:
        print(f"✗ Fixtures error: {e}")
        return False


if __name__ == "__main__":
    print("Running basic tests for onsen scraper...")

    tests = [
        test_imports,
        test_paths,
        test_constants,
        test_file_structure,
        test_data_mapper,
        test_mock_data,
        test_fixtures,
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
        print()

    if all_passed:
        print("🎉 All basic tests passed!")
        print("\nFor comprehensive testing, run:")
        print("  pytest tests/unit/test_data_mapper.py")
        print("  pytest tests/unit/test_scraper.py")
        print("  pytest tests/integration/test_scraper_integration.py")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
