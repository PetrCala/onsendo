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
