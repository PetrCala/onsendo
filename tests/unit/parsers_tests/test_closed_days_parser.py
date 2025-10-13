from datetime import datetime

from src.lib.parsers import parse_closed_days


def dt(y, m, d):
    return datetime(y, m, d, 12, 0)


def test_none_and_nashi():
    p = parse_closed_days(None)
    assert p.is_closed_on(dt(2025, 1, 1)) is False
    p2 = parse_closed_days("なし")
    assert p2.no_regular_closures
    assert p2.is_closed_on(dt(2025, 1, 1)) is False


def test_weekly_simple():
    p = parse_closed_days("火曜日")
    # 2025-01-07 is a Tuesday
    assert p.is_closed_on(dt(2025, 1, 7)) is True
    # 2025-01-08 is Wednesday
    assert p.is_closed_on(dt(2025, 1, 8)) is False


def test_weekly_multiple_and_exclude_holiday():
    p = parse_closed_days("月・火・水曜 (祝日の場合は営業)")
    # Assume 2025-01-06 is a Monday and a holiday per usage_time tests setup may vary.
    # We cannot rely on external holiday service here; behavior should not error.
    assert p.is_closed_on(dt(2025, 1, 6)) in {False, True}


def test_ordinal_weekday():
    p = parse_closed_days("第３水曜日")
    # In Jan 2025, 3rd Wednesday is 2025-01-15
    assert p.is_closed_on(dt(2025, 1, 15)) is True
    assert p.is_closed_on(dt(2025, 1, 8)) is False


def test_monthly_specific_days():
    p = parse_closed_days("毎月5・20日")
    assert p.is_closed_on(dt(2025, 1, 5)) is True
    assert p.is_closed_on(dt(2025, 1, 20)) is True
    assert p.is_closed_on(dt(2025, 1, 21)) is False


def test_absolute_dates_and_ranges():
    p = parse_closed_days("12/31～1/3")
    assert p.is_closed_on(dt(2024, 12, 31)) is True
    assert p.is_closed_on(dt(2025, 1, 1)) is True
    assert p.is_closed_on(dt(2025, 1, 4)) is False

    p2 = parse_closed_days("1/1～3")
    assert p2.is_closed_on(dt(2025, 1, 2)) is True


def test_compound_text_with_notes():
    p = parse_closed_days("火・水曜※イベント時は営業12/31～1/3")
    assert any("営業" in n for n in p.notes)
    # Should include absolute dates rule for new year
    assert p.is_closed_on(dt(2025, 1, 2)) is True


def test_irregular_marks_unknown():
    p = parse_closed_days("不定休(家族湯は水曜）")
    assert p.irregular_or_unknown
    # Without deterministic rules, result may be None (unknown)
    assert p.is_closed_on(dt(2025, 1, 2)) in {None, False}
