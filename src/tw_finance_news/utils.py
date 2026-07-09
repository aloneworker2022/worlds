from __future__ import annotations

import html
import re
from datetime import date, datetime, timedelta, timezone

# 台灣無日光節約時間，固定 UTC+8
TAIPEI_TZ = timezone(timedelta(hours=8), name="Asia/Taipei")

# Matches: （2330）、(2330)、（2330-TW）、2330-TW、TWS:2330:STOCK
_STOCK_CODE_RE = re.compile(
    r"[（(](\d{4,5})(?:-TW)?[）)]"
    r"|(?<!\d)(\d{4,5})-TW(?![a-zA-Z0-9])"
    r"|TWS:(\d{4,5}):\w+"
)


def extract_stock_codes(text: str) -> list[str]:
    """Extract Taiwan stock codes from text in various formats."""
    codes: set[str] = set()
    for m in _STOCK_CODE_RE.finditer(text):
        for g in m.groups():
            if g:
                codes.add(g)
    return sorted(codes)


def clean_html(raw: str) -> str:
    """Strip HTML tags and unescape entities, collapse whitespace."""
    unescaped = html.unescape(raw)
    stripped = re.sub(r"<[^>]+>", " ", unescaped)
    return re.sub(r"\s+", " ", stripped).strip()


def unix_to_datetime(ts: int) -> datetime:
    """Convert Unix timestamp to UTC-aware datetime."""
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def taipei_day_range(day: date) -> tuple[datetime, datetime]:
    """回傳台灣時間某一天的起訖時刻（含兩端，UTC-aware）。"""
    start = datetime(day.year, day.month, day.day, tzinfo=TAIPEI_TZ)
    end = start + timedelta(days=1) - timedelta(seconds=1)
    return start, end
