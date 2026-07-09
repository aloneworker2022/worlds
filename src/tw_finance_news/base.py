from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .models import NewsArticle, NewsSource, ScrapeResult

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


class BaseScraper(ABC):
    source: NewsSource
    _base_url: str
    _delay_seconds: float = 1.0

    def __init__(self, timeout: float = 15.0, delay: float | None = None):
        self._timeout = timeout
        if delay is not None:
            self._delay_seconds = delay
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "BaseScraper":
        self._client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=self._timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._client:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _get(self, url: str, **kwargs: object) -> httpx.Response:
        assert self._client, "Use as async context manager"
        resp = await self._client.get(url, **kwargs)
        resp.raise_for_status()
        return resp

    @abstractmethod
    async def _fetch_page(
        self,
        page: int = 1,
        *,
        stock_code: str | None = None,
        category: str | None = None,
        limit: int = 20,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> ScrapeResult: ...

    async def get_news_async(
        self,
        pages: int = 1,
        stock_code: str | None = None,
        category: str | None = None,
        limit: int = 20,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[NewsArticle]:
        """抓取新聞。start_at / end_at 需為 timezone-aware datetime，
        不支援伺服器端日期查詢的來源會在此以 published_at 過濾。"""
        all_articles: list[NewsArticle] = []
        async with self:
            for page in range(1, pages + 1):
                result = await self._fetch_page(
                    page,
                    stock_code=stock_code,
                    category=category,
                    limit=limit,
                    start_at=start_at,
                    end_at=end_at,
                )
                all_articles.extend(result.articles)
                if not result.has_more:
                    break
                if page < pages:
                    await asyncio.sleep(self._delay_seconds)

        if start_at is not None:
            all_articles = [a for a in all_articles if a.published_at >= start_at]
        if end_at is not None:
            all_articles = [a for a in all_articles if a.published_at <= end_at]
        return all_articles

    def get_news(
        self,
        pages: int = 1,
        stock_code: str | None = None,
        category: str | None = None,
        limit: int = 20,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[NewsArticle]:
        """Synchronous wrapper around get_news_async."""
        return asyncio.run(
            self.get_news_async(
                pages=pages,
                stock_code=stock_code,
                category=category,
                limit=limit,
                start_at=start_at,
                end_at=end_at,
            )
        )
