from __future__ import annotations

import asyncio
import datetime as dt
import logging

from .models import NewsArticle, NewsCategory, NewsSource
from .scrapers.cnyes import CnyesScraper
from .scrapers.moneydj import MoneyDJScraper
from .scrapers.statementdog import StatementDogScraper
from .scrapers.udn import UdnScraper
from .scrapers.yahoo import YahooFinanceScraper
from .utils import taipei_day_range

logger = logging.getLogger(__name__)

_SCRAPER_CLASSES = {
    NewsSource.CNYES: CnyesScraper,
    NewsSource.UDN: UdnScraper,
    NewsSource.MONEYDJ: MoneyDJScraper,
    NewsSource.YAHOO: YahooFinanceScraper,
    NewsSource.STATEMENTDOG: StatementDogScraper,
}


class NewsAggregator:
    """
    從多個台灣財經新聞來源並發抓取並整合結果。

    使用範例::

        # 同步
        articles = NewsAggregator().get_news(stock_code="2330")

        # 非同步
        articles = await NewsAggregator().get_news_async(stock_code="2330")

        # 指定日期（台灣時間的一整天）
        articles = NewsAggregator().get_news(date=datetime.date(2026, 7, 8))

        # 指定來源
        agg = NewsAggregator(sources=[NewsSource.CNYES, NewsSource.UDN])
        articles = agg.get_news()
    """

    def __init__(
        self,
        sources: list[NewsSource] | None = None,
        timeout: float = 20.0,
    ):
        self._sources = sources or list(NewsSource)
        self._timeout = timeout

    async def get_news_async(
        self,
        stock_code: str | None = None,
        category: NewsCategory | None = None,
        pages: int = 1,
        limit_per_source: int = 20,
        deduplicate: bool = True,
        date: dt.date | None = None,
    ) -> list[NewsArticle]:
        """並發抓取所有來源，合併後依時間排序。

        date 指定台灣時間的某一天；鉅亨網走 API 的 startAt/endAt，
        其餘來源只提供最新新聞，會以 published_at 過濾，
        因此非近日的歷史日期通常只有鉅亨網有結果。
        """
        start_at = end_at = None
        if date is not None:
            start_at, end_at = taipei_day_range(date)

        tasks = []
        for src in self._sources:
            cls = _SCRAPER_CLASSES[src]
            scraper = cls(timeout=self._timeout)
            tasks.append(
                scraper.get_news_async(
                    pages=pages,
                    stock_code=stock_code,
                    category=category.value if category else None,
                    limit=limit_per_source,
                    start_at=start_at,
                    end_at=end_at,
                )
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles: list[NewsArticle] = []
        for src, result in zip(self._sources, results):
            if isinstance(result, Exception):
                logger.warning("來源 %s 抓取失敗: %s", src.value, result)
                continue
            all_articles.extend(result)

        if deduplicate:
            seen: set[str] = set()
            deduped: list[NewsArticle] = []
            for a in all_articles:
                if a.article_id not in seen:
                    seen.add(a.article_id)
                    deduped.append(a)
            all_articles = deduped

        all_articles.sort(key=lambda a: a.published_at, reverse=True)
        return all_articles

    def get_news(
        self,
        stock_code: str | None = None,
        category: NewsCategory | None = None,
        pages: int = 1,
        limit_per_source: int = 20,
        deduplicate: bool = True,
        date: dt.date | None = None,
    ) -> list[NewsArticle]:
        """同步版本的 get_news_async。"""
        return asyncio.run(
            self.get_news_async(
                stock_code=stock_code,
                category=category,
                pages=pages,
                limit_per_source=limit_per_source,
                deduplicate=deduplicate,
                date=date,
            )
        )
