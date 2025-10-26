from datetime import datetime, date
import json
import os
import tempfile

from src.lib.parsers import parse_usage_time
from src.lib.parsers.usage_time import (
    MockHolidayService,
    JapanHolidayService,
    CachedJapanHolidayService,
    set_holiday_service,
    get_holiday_service,
    is_holiday,
)


def dt(y, m, d, h, mi):
    return datetime(y, m, d, h, mi)


def test_basic_single_window():
    p = parse_usage_time("11:00～21:00")
    assert not p.is_closed
    assert len(p.windows) == 1
    assert p.is_open(dt(2025, 1, 1, 12, 0))
    assert not p.is_open(dt(2025, 1, 1, 22, 0))


def test_two_windows():
    p = parse_usage_time("6:30～14:00/15:00～22:30")
    assert len(p.windows) == 2
    assert p.is_open(dt(2025, 1, 1, 6, 45))
    assert not p.is_open(dt(2025, 1, 1, 14, 5))
    assert p.is_open(dt(2025, 1, 1, 21, 0))


def test_cross_midnight():
    p = parse_usage_time("15:00〜深夜0:00")
    assert len(p.windows) == 1
    assert p.is_open(dt(2025, 1, 1, 23, 30))
    assert not p.is_open(dt(2025, 1, 2, 1, 0))


def test_seasonal():
    p = parse_usage_time(
        "(5～10月)6:00～11:50／14:00～22:50、(11～4月)6:30～11:50／14:00～22:50"
    )
    assert len(p.windows) >= 4
    scenarios = [
        # (datetime, expected_is_open, description)
        (dt(2025, 5, 2, 6, 0), True, "May at 6:00 open"),
        (dt(2025, 4, 2, 6, 0), False, "April at 6:00 closed"),
        (dt(2025, 5, 2, 12, 0), False, "May at 12:00 closed"),
        (dt(2025, 4, 2, 12, 0), False, "April at 12:00 closed"),
        (dt(2025, 5, 2, 20, 0), True, "May at 20:00 open"),
        (dt(2025, 4, 2, 20, 0), True, "April at 20:00 open"),
    ]
    for when, expected, desc in scenarios:
        assert p.is_open(when) == expected, desc


def test_weekday_weekend():
    p = parse_usage_time("平日14:00～17:00 日・祝15:00～17:00")
    scenarios = [
        # (datetime, expected_is_open, description)
        (dt(2025, 1, 3, 16, 0), True, "Friday 16:00 open"),
        (dt(2025, 1, 5, 14, 0), False, "Sunday 14:00 closed"),
        (dt(2025, 1, 5, 16, 0), True, "Sunday 16:00 open"),
        (dt(2025, 1, 1, 14, 0), False, "Holiday 14:00 closed"),
        (dt(2025, 1, 1, 15, 0), True, "Holiday 15:00 open"),
    ]
    for when, expected, desc in scenarios:
        assert p.is_open(when) == expected, desc


def test_hotel_in_out():
    p = parse_usage_time("IN15:00 OUT10:00")
    assert p.check_in_time is not None and p.check_out_time is not None


def test_closed_and_inquiry():
    p = parse_usage_time("休業中")
    assert p.is_closed
    p2 = parse_usage_time("11:00～15:00(要問合せ)")
    assert p2.requires_inquiry


def test_unknown():
    p = parse_usage_time(None)
    assert p.unknown_or_non_time


# Holiday-related tests
def test_mock_holiday_service():
    """Test the MockHolidayService class."""
    # Create mock holidays for 2025
    mock_holidays = {
        2025: {
            date(2025, 1, 1),  # New Year's Day
            date(2025, 1, 6),  # Coming of Age Day
            date(2025, 2, 11),  # National Foundation Day
        }
    }

    service = MockHolidayService(mock_holidays)

    # Test holiday detection
    assert service.get_holidays(2025) == mock_holidays[2025]
    assert service.get_holidays(2024) == set()  # No holidays for 2024
    assert service.get_holidays(2026) == set()  # No holidays for 2026


def test_holiday_service_global():
    """Test the global holiday service functionality."""
    # Set up mock service
    mock_holidays = {2025: {date(2025, 1, 1), date(2025, 1, 6)}}
    mock_service = MockHolidayService(mock_holidays)

    # Store original service
    original_service = get_holiday_service()

    try:
        # Set mock service
        set_holiday_service(mock_service)

        # Test holiday detection
        assert is_holiday(dt(2025, 1, 1, 12, 0))  # New Year's Day
        assert is_holiday(dt(2025, 1, 6, 12, 0))  # Coming of Age Day
        assert not is_holiday(dt(2025, 1, 2, 12, 0))  # Regular day
        assert not is_holiday(dt(2025, 2, 1, 12, 0))  # Regular day

    finally:
        # Restore original service
        set_holiday_service(original_service)


def test_holiday_aware_time_windows():
    """Test that time windows with holiday markers work correctly."""
    # Set up mock holidays
    mock_holidays = {
        2025: {
            date(2025, 1, 1),
            date(2025, 1, 6),
        }  # New Year's Day and Coming of Age Day
    }
    mock_service = MockHolidayService(mock_holidays)

    # Store original service
    original_service = get_holiday_service()

    try:
        set_holiday_service(mock_service)

        # Test "日・祝15:00～17:00" - should be open on Sundays and holidays
        p = parse_usage_time("日・祝15:00～17:00")

        scenarios = [
            # (datetime, expected_is_open, description)
            (dt(2025, 1, 5, 16, 0), True, "Sunday at 16:00"),
            (dt(2025, 1, 5, 14, 0), False, "Sunday at 14:00 (before opening)"),
            (dt(2025, 1, 1, 16, 0), True, "Holiday at 16:00"),
            (dt(2025, 1, 1, 14, 0), False, "Holiday at 14:00 (before opening)"),
            (dt(2025, 1, 2, 16, 0), False, "Thursday at 16:00 (regular weekday)"),
            (dt(2025, 1, 4, 16, 0), False, "Saturday at 16:00 (regular Saturday)"),
        ]
        for test_dt, expected, desc in scenarios:
            assert p.is_open(test_dt) == expected, f"Failed: {desc}"

    finally:
        set_holiday_service(original_service)


def test_holiday_only_windows():
    """Test time windows that are only open on holidays."""
    # Set up mock holidays
    mock_holidays = {2025: {date(2025, 1, 1), date(2025, 1, 6)}}
    mock_service = MockHolidayService(mock_holidays)

    # Store original service
    original_service = get_holiday_service()

    try:
        set_holiday_service(mock_service)

        # Test "祝15:00～17:00" - should only be open on holidays
        p = parse_usage_time("祝15:00～17:00")

        # Holiday (2025-01-01 is New Year's Day)
        assert p.is_open(dt(2025, 1, 1, 16, 0))  # Holiday at 16:00
        assert not p.is_open(dt(2025, 1, 1, 14, 0))  # Holiday at 14:00 (before opening)

        # Regular weekday (2025-01-02 is a Thursday)
        assert not p.is_open(dt(2025, 1, 2, 16, 0))  # Thursday at 16:00

        # Sunday (2025-01-05 is a Sunday, but not a holiday)
        assert not p.is_open(dt(2025, 1, 5, 16, 0))  # Sunday at 16:00

    finally:
        set_holiday_service(original_service)


def test_weekday_and_holiday_windows():
    """Test time windows that are open on weekdays and holidays."""
    # Set up mock holidays
    mock_holidays = {2025: {date(2025, 1, 1), date(2025, 1, 6)}}
    mock_service = MockHolidayService(mock_holidays)

    # Store original service
    original_service = get_holiday_service()

    try:
        set_holiday_service(mock_service)

        # Test "平日14:00～17:00 日・祝15:00～17:00" - weekdays 14-17, Sundays/holidays 15-17
        p = parse_usage_time("平日14:00～17:00 日・祝15:00～17:00")

        scenarios = [
            # (datetime, expected_is_open, description)
            (dt(2025, 1, 2, 16, 0), True, "Thursday at 16:00"),
            (dt(2025, 1, 2, 14, 30), True, "Thursday at 14:30"),
            (dt(2025, 1, 2, 13, 0), False, "Thursday at 13:00 (before opening)"),
            (dt(2025, 1, 5, 16, 0), True, "Sunday at 16:00"),
            (dt(2025, 1, 5, 14, 30), False, "Sunday at 14:30"),
            (dt(2025, 1, 5, 13, 0), False, "Sunday at 13:00 (before opening)"),
            (dt(2025, 1, 4, 16, 0), False, "Saturday at 16:00"),
            (dt(2025, 1, 4, 14, 30), False, "Saturday at 14:30"),
            (dt(2025, 1, 4, 13, 0), False, "Saturday at 13:00 (before opening)"),
            (dt(2025, 1, 1, 16, 0), True, "Holiday at 16:00 (New Year's Day)"),
            (dt(2025, 1, 1, 14, 30), False, "Holiday at 14:30 (New Year's Day)"),
            (
                dt(2025, 1, 1, 13, 0),
                False,
                "Holiday at 13:00 (New Year's Day) (before opening)",
            ),
        ]
        for test_dt, expected, desc in scenarios:
            assert p.is_open(test_dt) == expected, f"Failed: {desc}"

    finally:
        set_holiday_service(original_service)


def test_japan_holiday_service_initialization():
    """Test that JapanHolidayService can be initialized."""
    service = JapanHolidayService()
    assert service.base_url == "https://holidays-jp.github.io/api/v1"

    # Test with custom URL
    custom_service = JapanHolidayService("https://custom-url.com")
    assert custom_service.base_url == "https://custom-url.com"


def test_cached_holiday_service_initialization():
    """Test that CachedJapanHolidayService can be initialized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "test_cache.json")
        service = CachedJapanHolidayService(cache_file=cache_file)
        assert service.base_url == "https://holidays-jp.github.io/api/v1"
        assert service.cache_file == cache_file


def test_cached_holiday_service_memory_cache():
    """Test that CachedJapanHolidayService uses memory cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "test_cache.json")

        # Manually create cache file with test data
        test_holidays = {
            "years": {
                "2025": {
                    "2025-01-01": "元日",
                    "2025-01-13": "成人の日",
                    "2025-02-11": "建国記念の日"
                }
            },
            "metadata": {
                "2025": {"fetched_at": "2025-01-01T00:00:00"}
            }
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(test_holidays, f)

        # Create service and fetch holidays
        service = CachedJapanHolidayService(cache_file=cache_file)
        holidays_1 = service.get_holidays(2025)

        # Verify we got the holidays
        assert date(2025, 1, 1) in holidays_1
        assert date(2025, 1, 13) in holidays_1
        assert date(2025, 2, 11) in holidays_1
        assert len(holidays_1) == 3

        # Second call should use memory cache (no file read)
        holidays_2 = service.get_holidays(2025)
        assert holidays_1 == holidays_2


def test_cached_holiday_service_file_persistence():
    """Test that CachedJapanHolidayService persists cache across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "test_cache.json")

        # Manually create cache file with test data
        test_holidays = {
            "years": {
                "2024": {
                    "2024-01-01": "元日",
                    "2024-01-08": "成人の日"
                }
            },
            "metadata": {
                "2024": {"fetched_at": "2024-01-01T00:00:00"}
            }
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(test_holidays, f)

        # Create first service instance and fetch holidays
        service_1 = CachedJapanHolidayService(cache_file=cache_file)
        holidays_1 = service_1.get_holidays(2024)

        # Create second service instance (simulating app restart)
        service_2 = CachedJapanHolidayService(cache_file=cache_file)
        holidays_2 = service_2.get_holidays(2024)

        # Both should return the same holidays from cache
        assert holidays_1 == holidays_2
        assert date(2024, 1, 1) in holidays_2
        assert date(2024, 1, 8) in holidays_2


def test_cached_holiday_service_empty_cache():
    """Test that CachedJapanHolidayService handles empty/missing cache gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "nonexistent_cache.json")

        # Create service with non-existent cache file
        service = CachedJapanHolidayService(cache_file=cache_file)

        # The service should handle missing cache gracefully
        # (This will try to fetch from API, which may fail in test environment)
        # We're just testing that it doesn't crash
        assert service.cache_file == cache_file


def test_cached_holiday_service_corrupted_cache():
    """Test that CachedJapanHolidayService handles corrupted cache gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "corrupted_cache.json")

        # Create corrupted cache file
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write("{ this is not valid json }")

        # Create service with corrupted cache
        service = CachedJapanHolidayService(cache_file=cache_file)

        # The service should handle corrupted cache gracefully
        # (it should start with empty cache)
        assert service.cache_file == cache_file


def test_cached_holiday_service_cache_structure():
    """Test that CachedJapanHolidayService creates correct cache structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "test_cache.json")

        # Manually create cache with minimal data
        test_holidays = {
            "years": {
                "2023": {
                    "2023-01-01": "元日"
                }
            },
            "metadata": {
                "2023": {"fetched_at": "2023-01-01T00:00:00"}
            }
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(test_holidays, f)

        service = CachedJapanHolidayService(cache_file=cache_file)
        holidays = service.get_holidays(2023)

        # Verify the holiday was loaded correctly
        assert date(2023, 1, 1) in holidays

        # Verify cache file structure is preserved
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        assert "years" in cache_data
        assert "metadata" in cache_data
        assert "2023" in cache_data["years"]
