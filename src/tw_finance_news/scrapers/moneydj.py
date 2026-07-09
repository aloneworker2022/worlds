"""MoneyDJ 理財網新聞爬蟲 - 使用 RSS Feed"""
from __future__ import annotations

from datetime import datetime

from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

from ..base import BaseScraper
from ..models import NewsArticle, NewsCategory, NewsSource, ScrapeResult
from ..utils import extract_stock_codes

MONEYDJ_RSS_URLS: dict[str, str] = {
    "tw_stock": "https://www.moneydj.com/kmdj/RssCenter.aspx?svc=NW&fno=1&arg=X0000000",
    "us_stock": "https://www.moneydj.com/kmdj/RssCenter.aspx?svc=NW&fno=1&arg=X0000002",
    "fund": "https://www.moneydj.com/kmdj/RssCenter.aspx?svc=NW&fno=1&arg=X0000004",
}


class MoneyDJScraper(BaseScraper):
    """
    MoneyDJ 理財網 (moneydj.com) 新聞爬蟲

    使用 RSS Feed，每次最多 20 篇，不支援分頁。
    """

    source = NewsSource.MONEYDJ
    _base_url = "https://www.moneydj.com"
    _delay_seconds = 2.0

    async def _fetch_page(
        self,
        page: int = 1,
        *,
        stock_code: str | None = None,
        category: str | None = None,
        limit: int = 20,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> ScrapeResult:
        if page > 1:
            return ScrapeResult(articles=[], source=self.source, has_more=False)

        feed_url = MONEYDJ_RSS_URLS.get(category or "tw_stock", MONEYDJ_RSS_URLS["tw_stock"])
        resp = await self._get(feed_url)
        articles = self._parse_rss(resp.text)

        if stock_code:
            articles = [a for a in articles if stock_code in a.stock_codes]

        return ScrapeResult(
            articles=articles[:limit],
            source=self.source,
            has_more=False,
            total=len(articles),
        )

    def _parse_rss(self, xml_text: str) -> list[NewsArticle]:
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            return []
        articles = []
        for item in channel.findall("item"):
            try:
                articles.append(self._parse_item(item))
            except Exception:
                continue
        return articles

    def _parse_item(self, item: ET.Element) -> NewsArticle:
        title = (item.findtext("title") or "").strip()
        link = item.findtext("link") or ""
        guid = item.findtext("guid") or link
        pub_date = item.findtext("pubDate") or ""

        stock_codes = extract_stock_codes(title)
        published_at = parsedate_to_datetime(pub_date) if pub_date else None

        return NewsArticle(
            article_id=f"moneydj:{guid}",
            title=title,
            summary="",
            url=link,
            published_at=published_at,
            source=self.source,
            category=NewsCategory.TW_STOCK,
            stock_codes=stock_codes,
        )
