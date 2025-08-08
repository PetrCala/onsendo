from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import re
from typing import List, Optional, Set, Tuple

# Reuse helpers and holiday service from the usage time parser
from src.lib.parsers.usage_time import (
    normalize_text,
    DOW_MAP,
    is_holiday,
)


def _jp_num_to_int(token: str) -> Optional[int]:
    """Convert Japanese numeral tokens like '一二三四五六七八九十' or ASCII digits to int.

    Supports forms like '第３', '第2', '3', '３'. Returns None if not a number.
    """
    token = token.strip()
    if not token:
        return None
    # Standard digits
    if token.isdigit():
        return int(token)

    mapping = {
        "零": 0,
        "〇": 0,
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    # Simple cases up to 31 are enough for our use (days/ordinals)
    total = 0
    current = 0
    for ch in token:
        if ch == "十":
            current = max(1, current) * 10
            total += current
            current = 0
        elif ch in mapping and ch != "十":
            current += mapping[ch]
        else:
            return None
    total += current
    return total if total > 0 else None


# -------------------------------
# Rule types
# -------------------------------


class ClosedRule:
    """Interface for a closed-day rule.

    Implementations return True/False/None for a given datetime.
    None means unknown (cannot be determined from this rule alone).
    """

    def is_closed(self, dt: datetime) -> Optional[bool]:  # pragma: no cover - abstract
        raise NotImplementedError


@dataclass
class WeeklyClosedRule(ClosedRule):
    weekdays: Set[int]  # 0=Mon..6=Sun (can be empty when only holiday-based)
    closes_on_holidays_too: bool = False  # e.g., "土日祝日" or standalone 祝日
    shift_to_next_day_if_holiday: bool = False  # e.g., "祝日の場合は翌日"
    exclude_holidays: bool = False  # e.g., "祝日の場合は営業" / "祝祭日除く"

    def is_closed(self, dt: datetime) -> Optional[bool]:
        # Shift logic: if yesterday was the designated weekday and was holiday, today is closed
        if self.shift_to_next_day_if_holiday:
            yesterday = dt - timedelta(days=1)
            if yesterday.weekday() in self.weekdays and is_holiday(yesterday):
                return True

        # If today is the designated weekday
        if dt.weekday() in self.weekdays:
            # If shift applies and today is a holiday, closure moves to tomorrow -> not closed today
            if self.shift_to_next_day_if_holiday and is_holiday(dt):
                return False
            # If holidays are excluded, then do not close when today is a holiday
            if self.exclude_holidays and is_holiday(dt):
                return False
            return True

        # Holiday closure regardless of weekday
        if self.closes_on_holidays_too and is_holiday(dt):
            return True

        return False


@dataclass
class MonthlySpecificDaysRule(ClosedRule):
    days: Set[int]  # e.g., {5, 20}
    shift_to_next_day_if_holiday: bool = False

    def is_closed(self, dt: datetime) -> Optional[bool]:
        # Shift from yesterday if needed
        if self.shift_to_next_day_if_holiday:
            y = dt - timedelta(days=1)
            if y.day in self.days and is_holiday(y):
                return True

        if dt.day in self.days:
            if self.shift_to_next_day_if_holiday and is_holiday(dt):
                return False
            return True
        return False


@dataclass
class MonthlyOrdinalWeekdayRule(ClosedRule):
    ordinals: Set[int]  # e.g., {1, 3}
    weekday: int  # 0..6
    shift_to_next_day_if_holiday: bool = False

    def _nth_weekday_date(self, year: int, month: int, n: int) -> Optional[date]:
        # Find the date of the nth weekday in a given month
        # n >= 1
        # Compute first of month weekday offset
        d = date(year, month, 1)
        first_wd = d.weekday()
        # Days to add to reach first occurrence of self.weekday
        days_until = (self.weekday - first_wd) % 7
        day = 1 + days_until + (n - 1) * 7
        # Validate
        try:
            return date(year, month, day)
        except Exception:
            return None

    def _is_designated(self, d: date) -> bool:
        for n in self.ordinals:
            nd = self._nth_weekday_date(d.year, d.month, n)
            if nd and nd == d:
                return True
        return False

    def is_closed(self, dt: datetime) -> Optional[bool]:
        d = dt.date()
        # Shift from yesterday
        if self.shift_to_next_day_if_holiday:
            y = d - timedelta(days=1)
            if self._is_designated(y) and is_holiday(datetime(y.year, y.month, y.day)):
                return True

        if self._is_designated(d):
            if self.shift_to_next_day_if_holiday and is_holiday(dt):
                return False
            return True
        return False


@dataclass
class AbsoluteDatesRule(ClosedRule):
    """Specific (month, day) closures or inclusive ranges, evaluated annually.

    Ranges can cross months/years (e.g., 12/31～1/3).
    """

    # Single specific month/day pairs
    dates_mmdd: Set[Tuple[int, int]] = field(default_factory=set)
    # Ranges as (start_month, start_day, end_month, end_day)
    ranges: List[Tuple[int, int, int, int]] = field(default_factory=list)

    def _in_range(self, dt: date, s_m: int, s_d: int, e_m: int, e_d: int) -> bool:
        # Build concrete start/end around dt.year to account for wrap-around
        if (s_m, s_d) <= (e_m, e_d):
            # Non-wrapping window within the same year
            start = date(dt.year, s_m, s_d)
            end = date(dt.year, e_m, e_d)
            return start <= dt <= end
        # Wrapping window: consider two alignments (prev->curr) and (curr->next)
        start_prev = date(dt.year - 1, s_m, s_d)
        end_curr = date(dt.year, e_m, e_d)
        if start_prev <= dt <= end_curr:
            return True
        start_this = date(dt.year, s_m, s_d)
        end_next = date(dt.year + 1, e_m, e_d)
        return start_this <= dt <= end_next

    def is_closed(self, dt: datetime) -> Optional[bool]:
        d = (dt.month, dt.day)
        if d in self.dates_mmdd:
            return True
        for s_m, s_d, e_m, e_d in self.ranges:
            if self._in_range(dt.date(), s_m, s_d, e_m, e_d):
                return True
        return False


@dataclass
class ClosedDaysParsed:
    raw: Optional[str]
    normalized: Optional[str]

    rules: List[ClosedRule] = field(default_factory=list)
    no_regular_closures: bool = False  # "なし"
    irregular_or_unknown: bool = False  # 不定/不定休/臨時など
    requires_inquiry: bool = False
    notes: List[str] = field(default_factory=list)

    def is_closed_on(self, dt: Optional[datetime] = None) -> Optional[bool]:
        if dt is None:
            dt = datetime.now()
        # If explicitly no closures
        if self.no_regular_closures and not self.rules:
            return False
        # Evaluate rules - closed if any rule says closed
        any_known = False
        for rule in self.rules:
            r = rule.is_closed(dt)
            if r is True:
                return True
            if r is False:
                any_known = True
        if any_known:
            return False
        # Unknown if irregular and no deterministic rules
        if self.irregular_or_unknown and not self.rules:
            return None
        # Default to not closed when nothing is specified
        return False


# -------------------------------
# Parser
# -------------------------------


_RE_PARENS_SHIFT_NEXT = re.compile(r"祝(?:祭)?日の場合は?翌日")
_RE_EXCLUDE_HOLIDAYS = re.compile(r"(祝(?:祭)?日除く|祝(?:祭)?日の場合は営業)")


def _extract_shift_flag(s: str) -> Tuple[str, bool]:
    """Detect and remove the common parenthetical shift note.

    Returns (text_without_note, shift_flag)
    """
    shift = False
    # Match both full/half width parens already normalized by normalize_text
    m = re.search(r"\(([^)]*)\)", s)
    while m:
        inside = m.group(1)
        if _RE_PARENS_SHIFT_NEXT.search(inside):
            shift = True
            # remove this paren
            s = s[: m.start()] + s[m.end() :]
            m = re.search(r"\(([^)]*)\)", s)
        else:
            break
    return s.strip(), shift


def _extract_exclude_holidays_flag(s: str) -> Tuple[str, bool]:
    exclude = False
    # Look both in parens and after delimiters
    # Remove recognized token and return flag
    if _RE_EXCLUDE_HOLIDAYS.search(s):
        exclude = True
        s = _RE_EXCLUDE_HOLIDAYS.sub("", s)
    # Also check inside parenthesis blocks broadly
    m = re.search(r"\(([^)]*)\)", s)
    while m:
        inside = m.group(1)
        if _RE_EXCLUDE_HOLIDAYS.search(inside):
            exclude = True
            s = s[: m.start()] + s[m.end() :]
            m = re.search(r"\(([^)]*)\)", s)
        else:
            break
    return s.strip(), exclude


def _split_on_delimiters(s: str) -> List[str]:
    # Split on common separators while preserving content
    parts = re.split(r"[・,、／/]|\s+|※", s)
    return [p for p in (p.strip() for p in parts) if p]


def _parse_weekly_tokens(tokens: List[str]) -> Set[int]:
    days: Set[int] = set()
    for t in tokens:
        # Skip '毎月'
        if t.startswith("毎月"):
            continue
        m = re.fullmatch(r"(月|火|水|木|金|土|日)(?:曜|曜日)?", t)
        if m:
            days.add(DOW_MAP[m.group(1)])
    return days


def _parse_monthly_day_tokens(s: str) -> Optional[Set[int]]:
    # Expect forms like "毎月15日", "毎月5・20日", "毎月6・16・26日"
    m = re.match(r"毎月(?P<body>.+)", s)
    if not m:
        return None
    body = m.group("body")
    body = body.replace("日", "")
    body = body.replace(".", "・")
    nums = re.split(r"[・,、\s]+", body)
    out: Set[int] = set()
    for n in nums:
        if not n:
            continue
        v = _jp_num_to_int(n)
        if v:
            out.add(v)
    return out if out else None


def _parse_ordinal_weekday(s: str) -> Optional[Tuple[Set[int], int]]:
    # Examples: 第３水曜日, 第1第3水曜, 第1・3日曜日, 第2・第4水曜日
    # Normalize separators
    s2 = s
    # Quickly bail if no '第' and '曜'
    if "曜" not in s2 or "第" not in s2:
        return None
    # Extract weekday
    wd_m = re.search(r"(月|火|水|木|金|土|日)曜", s2)
    if not wd_m:
        return None
    weekday = DOW_MAP[wd_m.group(1)]
    # Extract all ordinals before weekday mention
    head = s2[: wd_m.start()]
    # Replace '第' with separator and strip
    head = head.replace("第", " ")
    nums = re.split(r"[・,、\s]+", head)
    ords: Set[int] = set()
    for n in nums:
        v = _jp_num_to_int(n)
        if v:
            ords.add(v)
    return (ords, weekday) if ords else None


def _parse_absolute_dates(s: str) -> Optional[AbsoluteDatesRule]:
    # Examples: "1/1～3", "12/31～1/3", "12/31", "12/30.31", "12/31、1/1〜3"
    text = s.replace(".", "・")
    dates: Set[Tuple[int, int]] = set()
    ranges: List[Tuple[int, int, int, int]] = []

    # Find ranges anywhere in the string (not only at the start)
    for m_rng in re.finditer(
        r"(?P<m1>\d{1,2})/(?P<d1>\d{1,2})\s*[~〜～\-]\s*(?:(?P<m2>\d{1,2})/)?(?P<d2>\d{1,2})",
        text,
    ):
        m1 = int(m_rng.group("m1"))
        d1 = int(m_rng.group("d1"))
        m2 = int(m_rng.group("m2")) if m_rng.group("m2") else m1
        d2 = int(m_rng.group("d2"))
        ranges.append((m1, d1, m2, d2))

    # Month with multiple days: 12/30・31
    for m_md_list in re.finditer(r"(?P<m>\d{1,2})/(?P<ds>[\d・]+)", text):
        m = int(m_md_list.group("m"))
        ds = m_md_list.group("ds")
        for d_tok in ds.split("・"):
            if d_tok.isdigit():
                dates.add((m, int(d_tok)))

    # Single exact dates M/D (avoid double-adding; sets handle dedup)
    for m_md in re.finditer(r"(?P<m>\d{1,2})/(?P<d>\d{1,2})", text):
        dates.add((int(m_md.group("m")), int(m_md.group("d"))))

    if dates or ranges:
        return AbsoluteDatesRule(dates_mmdd=dates, ranges=ranges)
    return None


def parse_closed_days(value: Optional[str]) -> ClosedDaysParsed:
    raw = value
    norm = normalize_text(value)
    result = ClosedDaysParsed(raw=raw, normalized=norm)

    if norm is None or norm == "" or norm.lower() in {"none", "null"}:
        # Treat as no information -> not explicitly closed
        result.no_regular_closures = False
        return result

    # Quick recognizers
    if "なし" in norm:
        result.no_regular_closures = True
    # Irregular patterns
    if any(k in norm for k in ["不定", "不定休", "臨時", "不定期"]):
        result.irregular_or_unknown = True
        # Often accompanied by requires inquiry/reservation
        if any(k in norm for k in ["要問合せ", "要確認", "要予約"]):
            result.requires_inquiry = True
    if any(k in norm for k in ["要問合せ", "要確認", "要予約"]):
        result.requires_inquiry = True
    if any(k in norm for k in ["悪天候", "雨天"]):
        result.requires_inquiry = True
        result.notes.append("weather dependent")

    # Split scope like '砂湯：...'
    scope_note = None
    if "：" in norm:
        scope_note, norm = norm.split("：", 1)
        scope_note = scope_note.strip()
        result.notes.append(f"scope:{scope_note}")

    # Some strings include trailing notes with '※'
    main_text = norm

    # Weekly closures with holiday shift note inside parens
    main_text, shift_flag = _extract_shift_flag(main_text)
    # Exclude-holiday flag (e.g., 祝日の場合は営業 / 祝祭日除く)
    main_text, exclude_holidays_flag = _extract_exclude_holidays_flag(main_text)

    # Detect weekend+holiday special form e.g., "土日祝日"
    if re.search(r"土日祝", main_text):
        result.rules.append(
            WeeklyClosedRule(weekdays={5, 6}, closes_on_holidays_too=True)
        )

    # Simple weekly day patterns (including lists like 水・木曜日, 月・火・水曜, 日曜)
    weekly_tokens = _split_on_delimiters(main_text)
    weekdays = _parse_weekly_tokens(weekly_tokens)
    if weekdays or exclude_holidays_flag:
        result.rules.append(
            WeeklyClosedRule(
                weekdays=weekdays,
                shift_to_next_day_if_holiday=shift_flag,
                exclude_holidays=exclude_holidays_flag,
            )
        )

    # Standalone '祝日' implies holiday-only closure
    if re.search(r"(^|[・,、\s])祝日($|[・,、\s])", main_text):
        result.rules.append(
            WeeklyClosedRule(weekdays=set(), closes_on_holidays_too=True)
        )

    # Ordinal weekday patterns like 第3水曜, 第1第3水曜, 第2・第4水曜日
    ow = _parse_ordinal_weekday(main_text)
    if ow:
        ords, wd = ow
        result.rules.append(
            MonthlyOrdinalWeekdayRule(
                ordinals=ords, weekday=wd, shift_to_next_day_if_holiday=shift_flag
            )
        )

    # Monthly specific days like 毎月15日 / 毎月5・20日 / 毎月6・16・26日
    mdays = _parse_monthly_day_tokens(main_text)
    if mdays:
        result.rules.append(
            MonthlySpecificDaysRule(days=mdays, shift_to_next_day_if_holiday=shift_flag)
        )

    # Absolute dates/ranges like 12/31～1/3, 1/1～3, 12/30.31
    abs_rule = _parse_absolute_dates(main_text)
    if abs_rule:
        result.rules.append(abs_rule)

    # New year vague mention
    if "年末年始" in norm and not abs_rule:
        result.irregular_or_unknown = True
        result.notes.append("new-year unspecified")

    # Combine: if text includes additional explicit absolute tokens after '※'
    extra_parts = re.split(r"※", norm)
    if len(extra_parts) > 1:
        for part in extra_parts[1:]:
            ar = _parse_absolute_dates(part)
            if ar:
                result.rules.append(ar)
            # Capture helpful notes
            if "営業" in part:
                result.notes.append(part.strip())

    return result


__all__ = [
    "ClosedRule",
    "WeeklyClosedRule",
    "MonthlySpecificDaysRule",
    "MonthlyOrdinalWeekdayRule",
    "AbsoluteDatesRule",
    "ClosedDaysParsed",
    "parse_closed_days",
]
