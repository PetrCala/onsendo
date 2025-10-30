"""Tests for Strava conversion utilities."""

from datetime import datetime, timezone

from src.lib.strava_converter import StravaFileExporter, StravaToActivityConverter
from src.types.strava import StravaStream, StravaActivityDetail


def _stream(stream_type: str, data: list | None) -> StravaStream:
    return StravaStream(
        stream_type=stream_type,
        data=data or [],
        original_size=len(data or []),
        resolution="high",
    )


def test_has_gpx_support_when_required_streams_present() -> None:
    streams = {
        "time": _stream("time", [0, 1, 2]),
        "latlng": _stream("latlng", [(35.0, 139.0), (35.1, 139.1), (35.2, 139.2)]),
    }

    assert StravaFileExporter.has_gpx_support(streams) is True


def test_has_gpx_support_missing_time_stream() -> None:
    streams = {
        "latlng": _stream("latlng", [(35.0, 139.0)]),
    }

    assert StravaFileExporter.has_gpx_support(streams) is False


def test_has_gpx_support_missing_latlng_stream() -> None:
    streams = {
        "time": _stream("time", [0, 1, 2]),
    }

    assert StravaFileExporter.has_gpx_support(streams) is False


def test_has_gpx_support_without_stream_data() -> None:
    streams = {
        "time": _stream("time", []),
        "latlng": _stream("latlng", []),
    }

    assert StravaFileExporter.has_gpx_support(streams) is False


def test_recommend_formats_gps_activity_with_hr() -> None:
    """Test format recommendation for GPS activity with heart rate."""
    streams = {
        "time": _stream("time", [0, 1, 2]),
        "latlng": _stream("latlng", [(35.0, 139.0), (35.1, 139.1)]),
        "heartrate": _stream("heartrate", [120, 125, 130]),
    }

    exportable, skipped = StravaFileExporter.recommend_formats(
        streams, ["gpx", "json", "hr_csv"]
    )

    assert exportable == ["gpx", "json", "hr_csv"]
    assert skipped == []


def test_recommend_formats_no_gps_with_hr() -> None:
    """Test format recommendation for heart rate monitoring activity (no GPS)."""
    streams = {
        "time": _stream("time", [0, 1, 2]),
        "heartrate": _stream("heartrate", [120, 125, 130]),
        "distance": _stream("distance", [0, 100, 200]),
    }

    exportable, skipped = StravaFileExporter.recommend_formats(
        streams, ["gpx", "json", "hr_csv"]
    )

    assert exportable == ["json", "hr_csv"]
    assert len(skipped) == 1
    assert skipped[0] == ("gpx", "No GPS data available")


def test_recommend_formats_gps_without_hr() -> None:
    """Test format recommendation for GPS activity without heart rate."""
    streams = {
        "time": _stream("time", [0, 1, 2]),
        "latlng": _stream("latlng", [(35.0, 139.0), (35.1, 139.1)]),
    }

    exportable, skipped = StravaFileExporter.recommend_formats(
        streams, ["gpx", "json", "hr_csv"]
    )

    assert exportable == ["gpx", "json"]
    assert len(skipped) == 1
    assert skipped[0] == ("hr_csv", "No heart rate data available")


def test_recommend_formats_minimal_activity() -> None:
    """Test format recommendation for minimal activity (no GPS, no HR)."""
    streams = {
        "time": _stream("time", [0, 1, 2]),
        "distance": _stream("distance", [0, 100, 200]),
    }

    exportable, skipped = StravaFileExporter.recommend_formats(
        streams, ["gpx", "json", "hr_csv"]
    )

    assert exportable == ["json"]
    assert len(skipped) == 2
    assert skipped[0] == ("gpx", "No GPS data available")
    assert skipped[1] == ("hr_csv", "No heart rate data available")


def test_recommend_formats_json_only_request() -> None:
    """Test when user explicitly requests only JSON."""
    streams = {
        "time": _stream("time", [0, 1, 2]),
    }

    exportable, skipped = StravaFileExporter.recommend_formats(streams, ["json"])

    assert exportable == ["json"]
    assert skipped == []


def test_recommend_formats_gpx_only_no_gps_fallback() -> None:
    """Test fallback to JSON when user requests GPX but no GPS available."""
    streams = {
        "time": _stream("time", [0, 1, 2]),
        "heartrate": _stream("heartrate", [120, 125, 130]),
    }

    exportable, skipped = StravaFileExporter.recommend_formats(streams, ["gpx"])

    # Should fallback to JSON when no formats are exportable
    assert exportable == ["json"]
    assert len(skipped) == 1
    assert skipped[0] == ("gpx", "No GPS data available")


def test_recommend_formats_empty_streams_fallback() -> None:
    """Test fallback to JSON when no streams are usable."""
    streams = {}

    exportable, skipped = StravaFileExporter.recommend_formats(
        streams, ["gpx", "hr_csv"]
    )

    # Should fallback to JSON as minimum viable export
    assert exportable == ["json"]
    assert len(skipped) == 2


# ============================================================================
# StravaToActivityConverter Tests - Heart Rate Time-Series
# ============================================================================


def _create_mock_activity(
    activity_id: int = 12345678,
    name: str = "Morning Run",
    activity_type: str = "Run",
    has_heartrate: bool = True,
) -> StravaActivityDetail:
    """Create a mock Strava activity for testing."""
    return StravaActivityDetail(
        id=activity_id,
        name=name,
        activity_type=activity_type,
        sport_type="Run",
        start_date=datetime(2025, 10, 30, 10, 0, 0, tzinfo=timezone.utc),
        start_date_local=datetime(2025, 10, 30, 19, 0, 0),  # JST = UTC+9
        timezone="(GMT+09:00) Asia/Tokyo",
        distance_m=5000,
        moving_time_s=1800,  # 30 minutes
        elapsed_time_s=1800,
        total_elevation_gain_m=50.0,
        calories=300,
        has_heartrate=has_heartrate,
        average_heartrate=145.0 if has_heartrate else None,
        max_heartrate=165.0 if has_heartrate else None,
        start_latlng=[33.279, 131.500],
        end_latlng=[33.282, 131.503],
        average_speed=2.78,  # 5km / 1800s
        max_speed=4.0,
        average_cadence=None,
        average_watts=None,
        average_temp=15.0,
        description="Beautiful morning run in Beppu",
        gear_id=None,
    )


def test_activity_converter_with_full_hr_timeseries() -> None:
    """Test Activity conversion includes complete HR time-series in route_data."""
    activity_detail = _create_mock_activity()
    streams = {
        "time": _stream("time", [0, 5, 10, 15, 20]),
        "heartrate": _stream("heartrate", [120, 125, 135, 145, 140]),
        "latlng": _stream(
            "latlng",
            [
                [33.279, 131.500],
                [33.280, 131.501],
                [33.281, 131.502],
                [33.282, 131.503],
                [33.283, 131.504],
            ],
        ),
        "altitude": _stream("altitude", [10.0, 15.0, 20.0, 25.0, 30.0]),
        "velocity_smooth": _stream("velocity_smooth", [3.0, 3.2, 3.5, 3.4, 3.1]),
    }

    activity_data = StravaToActivityConverter.convert(activity_detail, streams)

    # Check HR timeseries exists
    assert activity_data.route_data is not None
    assert len(activity_data.route_data) == 5

    # Check each point has HR data
    for i, point in enumerate(activity_data.route_data):
        assert "hr" in point, f"Point {i} missing 'hr' field"
        assert "timestamp" in point
        assert "lat" in point
        assert "lon" in point
        assert "elevation" in point
        assert "speed_mps" in point

    # Verify HR values are correct
    assert activity_data.route_data[0]["hr"] == 120
    assert activity_data.route_data[1]["hr"] == 125
    assert activity_data.route_data[2]["hr"] == 135
    assert activity_data.route_data[3]["hr"] == 145
    assert activity_data.route_data[4]["hr"] == 140

    # Verify summary statistics
    assert activity_data.avg_heart_rate == 145.0
    assert activity_data.min_heart_rate == 120.0  # Calculated from streams
    assert activity_data.max_heart_rate == 165.0  # From activity summary


def test_activity_converter_with_partial_hr_data() -> None:
    """Test Activity conversion when HR stream has fewer points than time stream."""
    activity_detail = _create_mock_activity()
    streams = {
        "time": _stream("time", [0, 5, 10, 15, 20]),
        "heartrate": _stream("heartrate", [120, 125, 135]),  # Only 3 HR values
        "latlng": _stream(
            "latlng",
            [
                [33.279, 131.500],
                [33.280, 131.501],
                [33.281, 131.502],
                [33.282, 131.503],
                [33.283, 131.504],
            ],
        ),
    }

    activity_data = StravaToActivityConverter.convert(activity_detail, streams)

    assert activity_data.route_data is not None
    assert len(activity_data.route_data) == 5

    # First 3 points should have HR
    assert activity_data.route_data[0]["hr"] == 120
    assert activity_data.route_data[1]["hr"] == 125
    assert activity_data.route_data[2]["hr"] == 135

    # Last 2 points should not have HR
    assert "hr" not in activity_data.route_data[3]
    assert "hr" not in activity_data.route_data[4]


def test_activity_converter_without_hr_stream() -> None:
    """Test Activity conversion when no HR data is available."""
    activity_detail = _create_mock_activity(has_heartrate=False)
    streams = {
        "time": _stream("time", [0, 5, 10]),
        "latlng": _stream(
            "latlng",
            [
                [33.279, 131.500],
                [33.280, 131.501],
                [33.281, 131.502],
            ],
        ),
    }

    activity_data = StravaToActivityConverter.convert(activity_detail, streams)

    assert activity_data.route_data is not None
    assert len(activity_data.route_data) == 3

    # No HR data in any point
    for point in activity_data.route_data:
        assert "hr" not in point

    # Summary statistics should be None
    assert activity_data.avg_heart_rate is None
    assert activity_data.min_heart_rate is None
    assert activity_data.max_heart_rate is None


def test_activity_converter_hr_only_no_gps() -> None:
    """Test Activity conversion for indoor activity with HR but no GPS."""
    activity_detail = _create_mock_activity(activity_type="VirtualRun")
    activity_detail.start_latlng = None
    activity_detail.end_latlng = None

    streams = {
        "time": _stream("time", [0, 5, 10, 15]),
        "heartrate": _stream("heartrate", [110, 120, 130, 125]),
        "distance": _stream("distance", [0, 100, 200, 300]),
    }

    activity_data = StravaToActivityConverter.convert(activity_detail, streams)

    assert activity_data.route_data is not None
    assert len(activity_data.route_data) == 4

    # Check HR is present but no GPS
    for i, point in enumerate(activity_data.route_data):
        assert "hr" in point
        assert point["hr"] == streams["heartrate"].data[i]
        assert "lat" not in point
        assert "lon" not in point

    # Verify indoor/outdoor classification
    assert activity_data.indoor_outdoor == "indoor"


def test_activity_converter_empty_hr_stream() -> None:
    """Test Activity conversion when HR stream exists but is empty."""
    activity_detail = _create_mock_activity()
    streams = {
        "time": _stream("time", [0, 5, 10]),
        "heartrate": _stream("heartrate", []),  # Empty HR stream
        "latlng": _stream(
            "latlng",
            [
                [33.279, 131.500],
                [33.280, 131.501],
                [33.281, 131.502],
            ],
        ),
    }

    activity_data = StravaToActivityConverter.convert(activity_detail, streams)

    assert activity_data.route_data is not None
    assert len(activity_data.route_data) == 3

    # No HR data in any point
    for point in activity_data.route_data:
        assert "hr" not in point


def test_activity_converter_min_hr_calculation() -> None:
    """Test that min HR is correctly calculated from streams."""
    activity_detail = _create_mock_activity()
    activity_detail.max_heartrate = 180.0
    activity_detail.average_heartrate = 150.0

    streams = {
        "time": _stream("time", [0, 5, 10, 15, 20]),
        "heartrate": _stream("heartrate", [145, 155, 160, 142, 148]),  # min = 142
    }

    activity_data = StravaToActivityConverter.convert(activity_detail, streams)

    # Min should be calculated from stream data
    assert activity_data.min_heart_rate == 142.0
    # Max and avg come from activity summary
    assert activity_data.max_heart_rate == 180.0
    assert activity_data.avg_heart_rate == 150.0


def test_activity_converter_hr_timeseries_timestamps() -> None:
    """Test that HR timeseries has correct timestamps."""
    activity_detail = _create_mock_activity()
    streams = {
        "time": _stream("time", [0, 60, 120, 180]),  # 0s, 1min, 2min, 3min
        "heartrate": _stream("heartrate", [120, 130, 140, 135]),
    }

    activity_data = StravaToActivityConverter.convert(activity_detail, streams)

    assert activity_data.route_data is not None
    assert len(activity_data.route_data) == 4

    # Check timestamps are ISO format and correctly offset
    assert activity_data.route_data[0]["timestamp"].startswith("2025-10-30T10:00:00")
    assert activity_data.route_data[1]["timestamp"].startswith("2025-10-30T10:01:00")
    assert activity_data.route_data[2]["timestamp"].startswith("2025-10-30T10:02:00")
    assert activity_data.route_data[3]["timestamp"].startswith("2025-10-30T10:03:00")


def test_activity_converter_route_data_json_serialization() -> None:
    """Test that route_data can be serialized to JSON string."""
    activity_detail = _create_mock_activity()
    streams = {
        "time": _stream("time", [0, 5, 10]),
        "heartrate": _stream("heartrate", [120, 125, 130]),
        "latlng": _stream(
            "latlng", [[33.279, 131.500], [33.280, 131.501], [33.281, 131.502]]
        ),
    }

    activity_data = StravaToActivityConverter.convert(activity_detail, streams)

    # Test JSON serialization
    route_json = activity_data.route_data_json
    assert route_json is not None
    assert isinstance(route_json, str)

    # Verify it's valid JSON and can be parsed back
    import json

    parsed = json.loads(route_json)
    assert isinstance(parsed, list)
    assert len(parsed) == 3
    assert parsed[0]["hr"] == 120
    assert parsed[1]["hr"] == 125
    assert parsed[2]["hr"] == 130
