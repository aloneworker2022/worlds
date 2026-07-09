from datetime import date, timezone

import pytest

from tw_finance_news.utils import (
    clean_html,
    extract_stock_codes,
    taipei_day_range,
    unix_to_datetime,
)


@pytest.mark.parametrize("text,expected", [
    ("台積電（2330）法說會", ["2330"]),
    ("台積電(2330)上漲", ["2330"]),
    ("2330-TW創高", ["2330"]),
    ("（2330-TW）強勢", ["2330"]),
    ("TWS:2330:STOCK:COMMON", ["2330"]),
    ("聯電（2303）與台積電（2330）", ["2303", "2330"]),
    ("大盤上漲，無個股", []),
    ("台積電（2330）聯發科（2454）重複（2330）", ["2330", "2454"]),
])
def test_extract_stock_codes(text, expected):
    assert extract_stock_codes(text) == expected


def test_clean_html_strips_tags():
    assert clean_html("<p>台積電<b>法說會</b></p>") == "台積電 法說會"


def test_clean_html_unescapes_entities():
    assert clean_html("台積電&amp;聯發科") == "台積電&聯發科"


def test_clean_html_collapses_whitespace():
    assert clean_html("  台積電   法說會  ") == "台積電 法說會"


def test_unix_to_datetime_utc_aware():
    dt = unix_to_datetime(1748995200)
    assert dt.tzinfo == timezone.utc
    assert dt.year == 2025


def test_taipei_day_range_covers_whole_day():
    start, end = taipei_day_range(date(2025, 6, 4))
    # 台北 2025-06-04 00:00 = UTC 2025-06-03 16:00
    assert start.astimezone(timezone.utc).isoformat() == "2025-06-03T16:00:00+00:00"
    assert end.astimezone(timezone.utc).isoformat() == "2025-06-04T15:59:59+00:00"


def test_taipei_day_range_contains_fixture_timestamps():
    start, end = taipei_day_range(date(2025, 6, 4))
    # 兩個 fixture 時間戳都落在台北 6/4
    assert start <= unix_to_datetime(1748991600) <= end
    assert start <= unix_to_datetime(1748995200) <= end
