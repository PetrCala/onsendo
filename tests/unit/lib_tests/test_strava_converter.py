"""Tests for Strava conversion utilities."""

from src.lib.strava_converter import StravaFileExporter
from src.types.strava import StravaStream


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
