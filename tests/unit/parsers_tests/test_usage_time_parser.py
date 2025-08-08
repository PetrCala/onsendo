from datetime import datetime

from src.lib.parsers import parse_usage_time


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
    # May at 7:00 open, April at 7:00 closed
    assert p.is_open(dt(2025, 5, 2, 7, 0))
    assert not p.is_open(dt(2025, 4, 2, 7, 0))


def test_weekday_weekend():
    p = parse_usage_time("平日14:00～17:00 日・祝15:00～17:00")
    # Friday
    assert p.is_open(dt(2025, 1, 3, 16, 0))
    # Sunday
    assert p.is_open(dt(2025, 1, 5, 16, 0))


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
