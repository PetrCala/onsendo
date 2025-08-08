from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, date
import re
import requests
from typing import List, Optional, Set, Tuple, Dict
from abc import ABC, abstractmethod


# -------------------------------
# Holiday Service
# -------------------------------


class HolidayService(ABC):
    """Abstract base class for holiday services."""

    @abstractmethod
    def get_holidays(self, year: int) -> Set[date]:
        """Return a set of holiday dates for the given year."""
        pass


class JapanHolidayService(HolidayService):
    """Service to fetch Japanese holidays from the internet."""

    def __init__(self, base_url: str = "https://holidays-jp.github.io/api/v1"):
        self.base_url = base_url

    def get_holidays(self, year: int) -> Set[date]:
        """Fetch Japanese holidays for the given year from the internet."""
        try:
            url = f"{self.base_url}/{year}/date.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            holidays_data = response.json()
            holidays = set()

            for holiday_date_str in holidays_data.keys():
                # Parse date string (format: "2025-01-01")
                holiday_date = datetime.strptime(holiday_date_str, "%Y-%m-%d").date()
                holidays.add(holiday_date)

            return holidays
        except Exception as e:
            # Log error and return empty set as fallback
            print(f"Warning: Failed to fetch holidays for {year}: {e}")
            return set()


class MockHolidayService(HolidayService):
    """Mock holiday service for testing."""

    def __init__(self, holidays: Optional[Dict[int, Set[date]]] = None):
        self.holidays = holidays or {}

    def get_holidays(self, year: int) -> Set[date]:
        """Return mock holidays for the given year."""
        return self.holidays.get(year, set())


# Global holiday service instance
_holiday_service: Optional[HolidayService] = None


def get_holiday_service() -> HolidayService:
    """Get the global holiday service instance."""
    global _holiday_service
    if _holiday_service is None:
        _holiday_service = JapanHolidayService()
    return _holiday_service


def set_holiday_service(service: HolidayService) -> None:
    """Set the global holiday service instance (useful for testing)."""
    global _holiday_service
    _holiday_service = service


def is_holiday(dt: datetime) -> bool:
    """Check if the given datetime is a holiday."""
    holiday_service = get_holiday_service()
    holidays = holiday_service.get_holidays(dt.year)
    return dt.date() in holidays


# -------------------------------
# Dataclasses
# -------------------------------


@dataclass
class MonthRange:
    start_month: int
    end_month: int

    def includes(self, month: int) -> bool:
        if self.start_month <= self.end_month:
            return self.start_month <= month <= self.end_month
        # Wrap-around such as 11-4
        return month >= self.start_month or month <= self.end_month


@dataclass
class TimeWindow:
    """Represents a single daily time window, optionally scoped by days-of-week and seasons.

    - start_time and end_time are within the same nominal day; if the window crosses midnight, set end_next_day=True.
    - If end_time is None, the end is not machine-determinable (e.g., until sunset); the evaluator will treat as unknown.
    - last_admission_time, if present, is informational; we still consider the facility open until end_time.
    """

    start_time: time
    end_time: Optional[time]
    end_next_day: bool = False
    days_of_week: Optional[Set[int]] = None  # 0=Mon .. 6=Sun
    month_ranges: List[MonthRange] = field(default_factory=list)
    last_admission_time: Optional[time] = None
    includes_holidays: bool = False
    notes: Optional[str] = None

    def applies_on(self, dt: datetime) -> bool:
        # Check if it's a holiday
        is_holiday_date = is_holiday(dt)

        # Check if the day-of-week applies
        day_applies = self.days_of_week is None or dt.weekday() in self.days_of_week

        # If days_of_week is None, it means "any day" (including holidays)
        if self.days_of_week is None:
            # If includes_holidays=True but no specific days, it means "holidays only"
            if self.includes_holidays:
                if not is_holiday_date:
                    return False
            # Only check month ranges
            if self.month_ranges:
                if not any(r.includes(dt.month) for r in self.month_ranges):
                    return False
            return True

        # If days_of_week is specified, handle holiday logic
        if is_holiday_date:
            # If it's a holiday and this window doesn't include holidays, it doesn't apply
            if not self.includes_holidays:
                return False
            # If it's a holiday and holidays are included, it applies regardless of day-of-week
            day_applies = True

        if not day_applies:
            return False

        if self.month_ranges:
            if not any(r.includes(dt.month) for r in self.month_ranges):
                return False
        return True

    def contains_time(self, dt: datetime) -> Optional[bool]:
        """Return True/False/None whether the time falls inside this window.
        None means the end cannot be evaluated (e.g., no deterministic end_time).
        """
        if not self.applies_on(dt):
            return False

        minute_of_day = dt.hour * 60 + dt.minute
        start_min = self.start_time.hour * 60 + self.start_time.minute
        if self.end_time is None:
            return None
        end_min = self.end_time.hour * 60 + self.end_time.minute

        if self.end_next_day or end_min < start_min:
            # Crosses midnight
            return minute_of_day >= start_min or minute_of_day < end_min
        return start_min <= minute_of_day < end_min


@dataclass
class UsageTimeParsed:
    raw: Optional[str]
    normalized: Optional[str]

    windows: List[TimeWindow] = field(default_factory=list)

    # Flags/metadata captured from strings
    is_closed: bool = False
    requires_inquiry: bool = False
    requires_reservation: bool = False
    unknown_or_non_time: bool = False

    # Hotel-like semantics
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None

    # Misc informational notes if something couldn't be structured
    notes: List[str] = field(default_factory=list)

    def is_open(
        self, dt: Optional[datetime] = None, assume_unknown_closed: bool = True
    ) -> bool:
        if self.is_closed:
            return False
        if dt is None:
            dt = datetime.now()
        if not self.windows:
            return False if assume_unknown_closed else False

        any_unknown = False
        for window in self.windows:
            result = window.contains_time(dt)
            if result is True:
                return True
            if result is None:
                any_unknown = True
        if any_unknown and not assume_unknown_closed:
            return True
        return False


# -------------------------------
# Parsing helpers
# -------------------------------


FULLWIDTH_TO_ASCII = str.maketrans(
    {
        "：": ":",
        "〜": "～",
        "－": "-",
        "ー": "-",
        "　": " ",
        "／": "/",
        "，": ",",
        "（": "(",
        "）": ")",
    }
)


JAPANESE_DIGITS = {
    "０": "0",
    "１": "1",
    "２": "2",
    "３": "3",
    "４": "4",
    "５": "5",
    "６": "6",
    "７": "7",
    "８": "8",
    "９": "9",
}


DOW_MAP = {"月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6}
WEEKDAY_SET = {0, 1, 2, 3, 4}
WEEKEND_SET = {5, 6}


TIME_RE = re.compile(r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?")


def normalize_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    out = text
    # Replace full-width digits
    for k, v in JAPANESE_DIGITS.items():
        out = out.replace(k, v)
    out = out.translate(FULLWIDTH_TO_ASCII)
    # Unify tildes to the same symbol
    out = out.replace("~", "～")
    # Remove redundant spaces around slashes/commas
    out = re.sub(r"\s*([,/])\s*", r"\1", out)
    # Collapse multiple spaces
    out = re.sub(r"\s+", " ", out).strip()
    return out


def parse_hhmm(token: str) -> Optional[time]:
    m = TIME_RE.fullmatch(token)
    if not m:
        return None
    hour = int(m.group("hour"))
    minute = int(m.group("minute") or 0)
    hour = max(0, min(hour, 23))
    minute = max(0, min(minute, 59))
    return time(hour=hour, minute=minute)


def parse_time_token(raw: str, is_end: bool = False) -> Tuple[Optional[time], bool]:
    """Parse a time token like '6:30', '深夜0:00', '翌11:00'.

    Returns (time_obj or None, end_next_day).
    """
    s = raw.strip()
    end_next_day = False
    if s.startswith("翌"):
        end_next_day = True
        s = s[1:]
    if s.startswith("深夜"):
        # 深夜0:00 ~ consider as 24:00 (next day 0:00)
        end_next_day = True or end_next_day
        s = s.replace("深夜", "")
    t = parse_hhmm(s)
    # Special-case: '0:00' as end may indicate next day end
    if is_end and t and (raw.startswith("深夜") or raw.startswith("翌")):
        end_next_day = True
    return t, end_next_day


def extract_dow_set(segment: str) -> Tuple[Optional[Set[int]], bool]:
    """Extract a set of days-of-week from a segment and whether holidays are included."""
    includes_holidays = False
    days: Optional[Set[int]] = None

    # Explicit ranges like 月～土
    m = re.search(
        r"(月|火|水|木|金|土|日)\s*[～~\-〜]\s*(月|火|水|木|金|土|日)", segment
    )
    if m:
        start = DOW_MAP[m.group(1)]
        end = DOW_MAP[m.group(2)]
        if start <= end:
            days = set(range(start, end + 1))
        else:
            days = set(list(range(start, 7)) + list(range(0, end + 1)))

    # Multiple explicit days like 火曜, 日曜, etc. (require '曜' to avoid month '月')
    tokens = re.findall(r"(月|火|水|木|金|土|日)曜", segment)
    if tokens:
        token_set = {DOW_MAP[t] for t in tokens}
        days = token_set if days is None else days.intersection(token_set)

    if "平日" in segment:
        days = WEEKDAY_SET if days is None else days.intersection(WEEKDAY_SET)
    if "土日" in segment or re.search(r"土[・・,、]?日", segment):
        weekend = WEEKEND_SET
        days = weekend if days is None else days.intersection(weekend)
    # Holidays
    if "祝日" in segment or "祝" in segment:
        includes_holidays = True
        # Common shorthand: 日・祝 -> Sundays and holidays (restrict days to Sunday)
        if re.search(r"日\s*[・,、/]\s*祝", segment):
            day = {DOW_MAP["日"]}
            days = day if days is None else days.intersection(day)

    return (set(days) if days is not None else None, includes_holidays)


def extract_month_ranges(segment: str) -> List[MonthRange]:
    ranges: List[MonthRange] = []
    # Patterns like (5～10月)
    for m in re.finditer(
        r"\(?(?P<s>\d{1,2})\s*[～~\-〜]\s*(?P<e>\d{1,2})月\)?", segment
    ):
        s = int(m.group("s"))
        e = int(m.group("e"))
        ranges.append(MonthRange(start_month=s, end_month=e))
    # Patterns like (10～3月)
    return ranges


def _split_statements(text: str) -> List[str]:
    # Split by Japanese commas that often separate statements while preserving qualifiers
    parts = re.split(r"(?:(?<=\))|(?<=\d))\s*[、,]\s*", text)
    return [p.strip() for p in parts if p.strip()]


def _split_windows(segment: str) -> List[str]:
    # Split multiple windows using / or ／ or comma
    parts = re.split(r"\s*[／/，,]\s*", segment)

    # If no splits found, try splitting on spaces when there are multiple time patterns
    if len(parts) == 1 and "～" in segment:
        # Look for patterns like "平日14:00～17:00 日・祝15:00～17:00"
        # Split on spaces that separate different time windows
        time_patterns = re.findall(
            r"[^\s]*\d{1,2}:\d{2}[～~\-〜]\d{1,2}:\d{2}[^\s]*", segment
        )
        if len(time_patterns) > 1:
            # Split on spaces that are between time patterns
            parts = re.split(r"\s+(?=[^\s]*\d{1,2}:\d{2})", segment)

    return [p.strip() for p in parts if p.strip()]


def extract_last_admission(segment: str) -> Optional[time]:
    m = re.search(r"最終?受付\s*(深夜)?(翌)?\s*(\d{1,2}[:：]?\d{0,2})", segment)
    if m:
        token = m.group(3).replace("：", ":")
        if ":" not in token:
            token = f"{int(token)}:00"
        t, _ = parse_time_token(("深夜" if m.group(1) else "") + token, is_end=True)
        return t
    # Pattern like '受付22:00'
    m2 = re.search(r"受付\s*(深夜)?(翌)?\s*(\d{1,2}[:：]?\d{0,2})", segment)
    if m2:
        token = m2.group(3).replace("：", ":")
        if ":" not in token:
            token = f"{int(token)}:00"
        t, _ = parse_time_token(("深夜" if m2.group(1) else "") + token, is_end=True)
        return t
    return None


def parse_usage_time(value: Optional[str]) -> UsageTimeParsed:
    """
    Parse a Japanese usage time string into a structured UsageTimeParsed object.

    This function interprets a wide variety of Japanese time expressions for business hours,
    including regular hours, seasonal hours, weekday/weekend/holiday variations, hotel check-in/out,
    and special flags such as "closed", "inquiry required", or "reservation required".

    Parameters
    ----------
    value : str or None
        The raw usage time string (in Japanese) to parse. Can be None.

    Returns
    -------
    UsageTimeParsed
        An object containing the parsed and normalized usage time information, including
        time windows, check-in/out times, and various flags.

    Examples
    --------
    Basic single window:
        >>> parse_usage_time("11:00～21:00").windows
        [TimeWindow(start_time=datetime.time(11, 0), end_time=datetime.time(21, 0), ...)]

    Multiple windows:
        >>> parse_usage_time("6:30～14:00/15:00～22:30").windows
        [TimeWindow(...), TimeWindow(...)]

    Seasonal hours:
        >>> parse_usage_time("(5～10月)6:00～11:50／14:00～22:50、(11～4月)6:30～11:50／14:00～22:50").windows
        [TimeWindow(...), ...]

    Weekday/weekend/holiday:
        >>> parse_usage_time("平日14:00～17:00 日・祝15:00～17:00").windows
        [TimeWindow(...), TimeWindow(...)]

    Hotel check-in/out:
        >>> p = parse_usage_time("IN15:00 OUT10:00")
        >>> p.check_in_time
        datetime.time(15, 0)
        >>> p.check_out_time
        datetime.time(10, 0)

    Closed or unknown:
        >>> parse_usage_time("休業中").is_closed
        True
        >>> parse_usage_time(None).unknown_or_non_time
        True

    Special flags:
        >>> parse_usage_time("11:00～15:00(要問合せ)").requires_inquiry
        True
        >>> parse_usage_time("11:00～15:00(要予約)").requires_reservation
        True

    Notes
    -----
    - Holiday/weekend logic depends on the configured holiday service.
    """

    raw = value
    normalized = normalize_text(value)
    result = UsageTimeParsed(raw=raw, normalized=normalized)

    if normalized is None or normalized == "" or normalized.lower() in {"none", "null"}:
        result.unknown_or_non_time = True
        return result

    # Quick outcome flags
    if "休業中" in normalized:
        result.is_closed = True
        return result
    if "滞在中" in normalized:
        # Treat as 24h open
        result.windows.append(
            TimeWindow(start_time=time(0, 0), end_time=time(0, 0), end_next_day=True)
        )
        return result
    if "24時間" in normalized or "24 時間" in normalized or "24時間営業" in normalized:
        result.windows.append(
            TimeWindow(start_time=time(0, 0), end_time=time(0, 0), end_next_day=True)
        )
        return result

    if "要問合せ" in normalized or "要確認" in normalized:
        result.requires_inquiry = True
    if "要予約" in normalized or "完全予約" in normalized:
        result.requires_reservation = True

    # Hotel check-in/out style
    m_hotel = re.search(
        r"IN\s*(\d{1,2}:\d{2})\s*OUT\s*(\d{1,2}:\d{2})", normalized, re.I
    )
    if not m_hotel:
        # Some variants without colon spacing
        m_hotel = re.search(
            r"IN\s*(\d{1,2}:\d{2})\s*.*?OUT\s*(\d{1,2}:\d{2})", normalized, re.I
        )
    if m_hotel:
        result.check_in_time = parse_hhmm(m_hotel.group(1))
        result.check_out_time = parse_hhmm(m_hotel.group(2))

    # Break into top-level statements (handle seasonal qualifiers)
    statements = _split_statements(normalized)
    # If no commas, keep full text
    if not statements:
        statements = [normalized]

    for statement in statements:
        month_ranges = extract_month_ranges(statement)
        # Split into individual windows by '/', '／', or commas not already split
        for part in _split_windows(statement):
            # Days/holidays may be specified per sub-part like "日・祝15:00～17:00"
            part_days_set, part_includes_holidays = extract_dow_set(part)
            # Extract last admission if present inside the same part
            last_adm = extract_last_admission(part)

            # Try to find explicit time range with ～ or 〜 or -
            # Also support tokens like '10:00～受付22:00' by normalizing '受付22:00' to time
            part_norm = part
            part_norm = re.sub(
                r"受付\s*(深夜)?(翌)?\s*(\d{1,2}[:：]?\d{0,2})",
                lambda m: (
                    ("深夜" if m.group(1) else "")
                    + (
                        m.group(3).replace("：", ":")
                        if ":" in m.group(3)
                        else f"{int(m.group(3))}:00"
                    )
                ),
                part_norm,
            )

            # Skip obvious non-time statements like prices
            if re.search(r"\d+\s*円", part_norm):
                result.notes.append(part)
                continue

            # Windows like '9:00～日没まで' -> we cannot evaluate end
            if "日没" in part_norm:
                start_m = re.search(r"(\d{1,2}:\d{2})\s*[～~\-〜]", part_norm)
                if start_m:
                    st, _ = parse_time_token(start_m.group(1))
                    # Qualifiers only from text before the time range
                    prefix = part_norm[: start_m.start()]
                    local_days_set, local_includes_holidays = extract_dow_set(prefix)
                    result.windows.append(
                        TimeWindow(
                            start_time=st or time(0, 0),
                            end_time=None,
                            end_next_day=False,
                            days_of_week=(
                                set(local_days_set)
                                if local_days_set is not None
                                else (set(part_days_set) if part_days_set else None)
                            ),
                            month_ranges=list(month_ranges),
                            last_admission_time=last_adm,
                            includes_holidays=local_includes_holidays
                            or part_includes_holidays,
                            notes="ends at sunset",
                        )
                    )
                continue

            matched_any = False
            for m in re.finditer(
                r"(\d{1,2}:\d{2})\s*[～~\-〜]\s*(翌)?(深夜)?(\d{1,2}:\d{2})",
                part_norm,
            ):
                start_raw = m.group(1)
                end_prefix翌 = bool(m.group(2))
                end_prefix深夜 = bool(m.group(3))
                end_raw = m.group(4)

                st, _ = parse_time_token(start_raw)
                et, end_next_day = parse_time_token(
                    ("翌" if end_prefix翌 else "")
                    + ("深夜" if end_prefix深夜 else "")
                    + end_raw,
                    is_end=True,
                )
                if st is None or et is None:
                    continue

                # If end is earlier than start and not explicitly marked, treat as crossing midnight
                if not end_next_day and et <= st:
                    end_next_day = True

                # Determine qualifiers from prefix local to this range; fallback to part-level
                prefix = part_norm[: m.start()]
                local_days_set, local_includes_holidays = extract_dow_set(prefix)

                result.windows.append(
                    TimeWindow(
                        start_time=st,
                        end_time=et,
                        end_next_day=end_next_day,
                        days_of_week=(
                            set(local_days_set)
                            if local_days_set is not None
                            else (set(part_days_set) if part_days_set else None)
                        ),
                        month_ranges=list(month_ranges),
                        last_admission_time=last_adm,
                        includes_holidays=local_includes_holidays
                        or part_includes_holidays,
                    )
                )
                matched_any = True

            if matched_any:
                continue

            # Single time like '10:00～22:00' may be split above; nothing found -> try ranges with no minutes in end like '7:00〜9:00、15:00〜21:45'
            m2 = re.findall(
                r"\d{1,2}:\d{2}\s*[～~\-〜]\s*(?:翌|深夜)?\d{1,2}:\d{2}", part_norm
            )
            if m2:
                for rng in m2:
                    a, b = re.split(r"[～~\-〜]", rng)
                    b = b.strip()
                    st, _ = parse_time_token(a)
                    et, end_next_day = parse_time_token(b, is_end=True)
                    if st and et:
                        if not end_next_day and et <= st:
                            end_next_day = True
                        # For multi-ranges found this way, use part-level qualifiers
                        result.windows.append(
                            TimeWindow(
                                start_time=st,
                                end_time=et,
                                end_next_day=end_next_day,
                                days_of_week=(
                                    set(part_days_set) if part_days_set else None
                                ),
                                month_ranges=list(month_ranges),
                                last_admission_time=last_adm,
                                includes_holidays=part_includes_holidays,
                            )
                        )
                continue

            # If we got here and still no windows, record as note
            # This could be a qualifier-only segment like '日曜'
            if part.strip():
                result.notes.append(part.strip())

    if not result.windows and not result.is_closed:
        result.unknown_or_non_time = True

    return result


__all__ = [
    "MonthRange",
    "TimeWindow",
    "UsageTimeParsed",
    "parse_usage_time",
    "HolidayService",
    "JapanHolidayService",
    "MockHolidayService",
    "get_holiday_service",
    "set_holiday_service",
    "is_holiday",
]
