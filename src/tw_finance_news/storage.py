from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import NewsArticle, NewsCategory, NewsSource

_CSV_FIELDS = [
    "article_id", "title", "summary", "content", "url",
    "published_at", "source", "category", "stock_codes", "tags", "cover_image_url",
]


def _article_to_row(a: NewsArticle) -> dict:
    return {
        "article_id": a.article_id,
        "title": a.title,
        "summary": a.summary,
        "content": a.content,
        "url": a.url,
        "published_at": a.published_at.isoformat(),
        "source": a.source.value,
        "category": a.category.value,
        "stock_codes": "|".join(a.stock_codes),
        "tags": "|".join(a.tags),
        "cover_image_url": a.cover_image_url or "",
    }


def _row_to_article(row: dict) -> NewsArticle:
    return NewsArticle(
        article_id=row["article_id"],
        title=row["title"],
        summary=row.get("summary", ""),
        content=row.get("content", ""),
        url=row["url"],
        published_at=datetime.fromisoformat(row["published_at"]),
        source=NewsSource(row["source"]),
        category=NewsCategory(row["category"]),
        stock_codes=[c for c in row.get("stock_codes", "").split("|") if c],
        tags=[t for t in row.get("tags", "").split("|") if t],
        cover_image_url=row.get("cover_image_url") or None,
    )


class CsvStorage:
    """
    將新聞文章儲存到 CSV 檔案。

    使用範例::

        storage = CsvStorage("news.csv")
        added = storage.save(articles)   # 回傳新增筆數（自動去重）
        all_articles = storage.load()
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, articles: list[NewsArticle]) -> int:
        """儲存文章，跳過 article_id 已存在的，回傳新增筆數。"""
        existing_ids: set[str] = set()
        existing_rows: list[dict] = []

        if self.path.exists():
            with self.path.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    existing_ids.add(row["article_id"])
                    existing_rows.append(row)

        new_articles = [a for a in articles if a.article_id not in existing_ids]
        if not new_articles:
            return 0

        write_header = not self.path.exists() or self.path.stat().st_size == 0
        with self.path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
            if write_header:
                writer.writeheader()
            for article in new_articles:
                writer.writerow(_article_to_row(article))

        return len(new_articles)

    def load(self) -> list[NewsArticle]:
        """讀取所有已存文章，依發布時間降序排列。"""
        if not self.path.exists():
            return []
        articles = []
        with self.path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    articles.append(_row_to_article(row))
                except Exception:
                    continue
        articles.sort(key=lambda a: a.published_at, reverse=True)
        return articles


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS articles (
    article_id      TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    summary         TEXT DEFAULT '',
    content         TEXT DEFAULT '',
    url             TEXT NOT NULL,
    published_at    TEXT NOT NULL,
    source          TEXT NOT NULL,
    category        TEXT NOT NULL,
    stock_codes     TEXT DEFAULT '[]',
    tags            TEXT DEFAULT '[]',
    cover_image_url TEXT
)
"""

_INSERT = """
INSERT OR IGNORE INTO articles
    (article_id, title, summary, content, url, published_at, source, category,
     stock_codes, tags, cover_image_url)
VALUES
    (:article_id, :title, :summary, :content, :url, :published_at, :source, :category,
     :stock_codes, :tags, :cover_image_url)
"""


class SqliteStorage:
    """
    將新聞文章儲存到 SQLite 資料庫。

    使用範例::

        db = SqliteStorage("news.db")
        added = db.save(articles)
        recent = db.load(stock_code="2330", days=7)
        print(db.count())
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)

    def save(self, articles: list[NewsArticle]) -> int:
        """儲存文章，自動跳過已存在的 article_id，回傳新增筆數。"""
        rows = []
        for a in articles:
            rows.append({
                "article_id": a.article_id,
                "title": a.title,
                "summary": a.summary,
                "content": a.content,
                "url": a.url,
                "published_at": a.published_at.isoformat(),
                "source": a.source.value,
                "category": a.category.value,
                "stock_codes": json.dumps(a.stock_codes, ensure_ascii=False),
                "tags": json.dumps(a.tags, ensure_ascii=False),
                "cover_image_url": a.cover_image_url,
            })

        with self._connect() as conn:
            before = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
            conn.executemany(_INSERT, rows)
            after = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]

        return after - before

    def load(
        self,
        *,
        stock_code: str | None = None,
        source: str | None = None,
        days: int | None = None,
    ) -> list[NewsArticle]:
        """查詢已存文章，依發布時間降序排列。"""
        conditions: list[str] = []
        params: list[object] = []

        if stock_code:
            # stock_codes 是 JSON array，用 LIKE 搜尋
            conditions.append("stock_codes LIKE ?")
            params.append(f'%"{stock_code}"%')

        if source:
            conditions.append("source = ?")
            params.append(source)

        if days is not None:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            conditions.append("published_at >= ?")
            params.append(cutoff)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM articles {where} ORDER BY published_at DESC"

        articles = []
        with self._connect() as conn:
            for row in conn.execute(sql, params):
                try:
                    articles.append(_sqlite_row_to_article(dict(row)))
                except Exception:
                    continue
        return articles

    def count(self) -> int:
        """回傳資料庫中的文章總數。"""
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]


def _sqlite_row_to_article(row: dict) -> NewsArticle:
    return NewsArticle(
        article_id=row["article_id"],
        title=row["title"],
        summary=row.get("summary", ""),
        content=row.get("content", ""),
        url=row["url"],
        published_at=datetime.fromisoformat(row["published_at"]),
        source=NewsSource(row["source"]),
        category=NewsCategory(row["category"]),
        stock_codes=json.loads(row.get("stock_codes") or "[]"),
        tags=json.loads(row.get("tags") or "[]"),
        cover_image_url=row.get("cover_image_url") or None,
    )
