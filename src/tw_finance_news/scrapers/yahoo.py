"""Yahoo 奇摩股市新聞爬蟲 - 使用 RSS Feed"""
from __future__ import annotations

from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

from ..base import BaseScraper
from ..models import NewsArticle, NewsCategory, NewsSource, ScrapeResult
from ..utils import extract_stock_codes

YAHOO_RSS_URLS: dict[str, str] = {
    "tw_stock": "https://tw.stock.yahoo.com/rss?category=tw-market",
    "tw_news": "https://tw.stock.yahoo.com/rss?category=tw-stock-news",
}


class YahooFinanceScraper(BaseScraper):
    """
    Yahoo 奇摩股市 (tw.stock.yahoo.com) 新聞爬蟲

    使用 RSS Feed，每次最多 50 篇，不支援分頁。
    """

    source = NewsSource.YAHOO
    _base_url = "https://tw.stock.yahoo.com"
    _delay_seconds = 2.0

    async def _fetch_page(
        self,
        page: int = 1,
        *,
        stock_code: str | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> ScrapeResult:
        if page > 1:
            return ScrapeResult(articles=[], source=self.source, has_more=False)

        feed_url = YAHOO_RSS_URLS.get(category or "tw_stock", YAHOO_RSS_URLS["tw_stock"])
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
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        pub_date = item.findtext("pubDate") or ""

        stock_codes = extract_stock_codes(title + " " + desc)
        published_at = parsedate_to_datetime(pub_date) if pub_date else None

        url_path = link.split("?")[0]
        url_id = url_path.rstrip("/").rsplit("/", 1)[-1] or str(hash(link))

        return NewsArticle(
            article_id=f"yahoo:{url_id}",
            title=title,
            summary=desc[:300],
            url=link,
            published_at=published_at,
            source=self.source,
            category=NewsCategory.TW_STOCK,
            stock_codes=stock_codes,
        )
