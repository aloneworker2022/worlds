import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from tw_finance_news.models import NewsArticle, NewsCategory, NewsSource
from tw_finance_news.storage import CsvStorage, SqliteStorage


def make_article(
    article_id: str = "cnyes:1",
    source: NewsSource = NewsSource.CNYES,
    stock_codes: list[str] | None = None,
    days_ago: int = 0,
) -> NewsArticle:
    return NewsArticle(
        article_id=article_id,
        title=f"測試新聞 {article_id}",
        url=f"https://example.com/{article_id}",
        published_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        source=source,
        category=NewsCategory.TW_STOCK,
        stock_codes=stock_codes or [],
        tags=["AI", "台股"],
    )


# ── CsvStorage ────────────────────────────────────────────────────────────────

def test_csv_save_and_load(tmp_path):
    path = tmp_path / "news.csv"
    storage = CsvStorage(path)
    articles = [make_article("cnyes:1"), make_article("udn:2", NewsSource.UDN)]

    added = storage.save(articles)
    assert added == 2

    loaded = storage.load()
    assert len(loaded) == 2
    assert {a.article_id for a in loaded} == {"cnyes:1", "udn:2"}


def test_csv_deduplicates_on_second_save(tmp_path):
    path = tmp_path / "news.csv"
    storage = CsvStorage(path)
    a = make_article("cnyes:1")

    storage.save([a])
    added = storage.save([a, make_article("cnyes:2")])
    assert added == 1

    loaded = storage.load()
    assert len(loaded) == 2


def test_csv_preserves_stock_codes(tmp_path):
    path = tmp_path / "news.csv"
    storage = CsvStorage(path)
    a = make_article("cnyes:1", stock_codes=["2330", "2317"])

    storage.save([a])
    loaded = storage.load()
    assert loaded[0].stock_codes == ["2317", "2330"]


def test_csv_empty_file_returns_empty_list(tmp_path):
    storage = CsvStorage(tmp_path / "missing.csv")
    assert storage.load() == []


def test_csv_sorted_newest_first(tmp_path):
    path = tmp_path / "news.csv"
    storage = CsvStorage(path)
    old = make_article("cnyes:1", days_ago=2)
    new = make_article("cnyes:2", days_ago=0)

    storage.save([old, new])
    loaded = storage.load()
    assert loaded[0].article_id == "cnyes:2"


# ── SqliteStorage ─────────────────────────────────────────────────────────────

def test_sqlite_save_and_load(tmp_path):
    db = SqliteStorage(tmp_path / "news.db")
    articles = [make_article("cnyes:1"), make_article("udn:2", NewsSource.UDN)]

    added = db.save(articles)
    assert added == 2
    assert db.count() == 2


def test_sqlite_insert_or_ignore(tmp_path):
    db = SqliteStorage(tmp_path / "news.db")
    a = make_article("cnyes:1")

    db.save([a])
    added = db.save([a, make_article("cnyes:2")])
    assert added == 1
    assert db.count() == 2


def test_sqlite_load_filter_by_stock(tmp_path):
    db = SqliteStorage(tmp_path / "news.db")
    db.save([
        make_article("cnyes:1", stock_codes=["2330"]),
        make_article("cnyes:2", stock_codes=["2317"]),
        make_article("cnyes:3", stock_codes=["2330", "2317"]),
    ])

    results = db.load(stock_code="2330")
    assert len(results) == 2
    assert all("2330" in a.stock_codes for a in results)


def test_sqlite_load_filter_by_source(tmp_path):
    db = SqliteStorage(tmp_path / "news.db")
    db.save([
        make_article("cnyes:1", NewsSource.CNYES),
        make_article("udn:1", NewsSource.UDN),
    ])

    results = db.load(source="cnyes")
    assert len(results) == 1
    assert results[0].source == NewsSource.CNYES


def test_sqlite_load_filter_by_days(tmp_path):
    db = SqliteStorage(tmp_path / "news.db")
    db.save([
        make_article("cnyes:1", days_ago=1),   # 1 天前，在範圍內
        make_article("cnyes:2", days_ago=10),  # 10 天前，超出範圍
    ])

    results = db.load(days=3)
    assert len(results) == 1
    assert results[0].article_id == "cnyes:1"


def test_sqlite_load_sorted_newest_first(tmp_path):
    db = SqliteStorage(tmp_path / "news.db")
    db.save([
        make_article("cnyes:1", days_ago=2),
        make_article("cnyes:2", days_ago=0),
    ])

    results = db.load()
    assert results[0].article_id == "cnyes:2"


def test_sqlite_preserves_tags(tmp_path):
    db = SqliteStorage(tmp_path / "news.db")
    a = make_article("cnyes:1")  # tags=["AI", "台股"]
    db.save([a])

    loaded = db.load()[0]
    assert "AI" in loaded.tags
    assert "台股" in loaded.tags
