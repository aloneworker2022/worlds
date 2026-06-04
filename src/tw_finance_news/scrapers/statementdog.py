"""財報狗新聞爬蟲 - HTML 解析"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from ..base import BaseScraper
from ..models import NewsArticle, NewsCategory, NewsSource, ScrapeResult
from ..utils import extract_stock_codes

# 財報狗文章頁面內的股票代碼連結格式：/analysis/2330/...
_ANALYSIS_STOCK_RE = re.compile(r"/analysis/(\d{4,5})/")


class StatementDogScraper(BaseScraper):
    """
    財報狗 (statementdog.com) 新聞爬蟲

    Server-side rendered HTML，CSS class 穩定。
    提供兩個頁面：/news (熱門) 和 /news/latest (最新)。
    """

    source = NewsSource.STATEMENTDOG
    _base_url = "https://statementdog.com"
    _delay_seconds = 2.0

    async def _fetch_page(
        self,
        page: int = 1,
        *,
        stock_code: str | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> ScrapeResult:
        if page > 2:
            return ScrapeResult(articles=[], source=self.source, has_more=False)

        url = f"{self._base_url}/news/latest" if page == 2 else f"{self._base_url}/news"
        resp = await self._get(url)
        articles = self._parse_html(resp.text)

        if stock_code:
            articles = [a for a in articles if stock_code in a.stock_codes]

        return ScrapeResult(
            articles=articles[:limit],
            source=self.source,
            has_more=(page == 1),
            total=None,
        )

    def _parse_html(self, html: str) -> list[NewsArticle]:
        soup = BeautifulSoup(html, "lxml")
        items = soup.find_all("li", class_=re.compile(r"statementdog-news-list-item"))
        if not items:
            # fallback: try article cards
            items = soup.find_all("article")
        articles = []
        for item in items:
            try:
                articles.append(self._parse_item(item))
            except Exception:
                continue
        return articles

    def _parse_item(self, item: object) -> NewsArticle:
        link_tag = item.find("a")
        href = link_tag.get("href", "") if link_tag else ""

        # Try data-title first, then h2, then link text
        title = ""
        if link_tag:
            title = link_tag.get("data-title") or ""
        if not title:
            h2 = item.find(["h2", "h3"])
            title = h2.get_text(strip=True) if h2 else (link_tag.get_text(strip=True) if link_tag else "")

        date_tag = item.find(["time", "p"], class_=re.compile(r"date|time", re.I))
        date_str = ""
        if date_tag:
            date_str = date_tag.get("datetime") or date_tag.get_text(strip=True)

        desc_tag = item.find("p", class_=re.compile(r"desc|summary|content|excerpt", re.I))
        summary = desc_tag.get_text(strip=True) if desc_tag else ""

        news_id = href.rstrip("/").rsplit("/", 1)[-1] if href else ""

        published_at: datetime
        for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"):
            try:
                published_at = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                break
            except ValueError:
                continue
        else:
            published_at = datetime.now(timezone.utc)

        url = f"{self._base_url}{href}" if href.startswith("/") else (href or self._base_url)

        stock_codes = extract_stock_codes(title + " " + summary)
        # 從連結 href 路徑抽取 analysis 股票代碼
        if href:
            for code in _ANALYSIS_STOCK_RE.findall(href):
                if code not in stock_codes:
                    stock_codes.append(code)

        return NewsArticle(
            article_id=f"statementdog:{news_id}",
            title=title,
            summary=summary,
            url=url,
            published_at=published_at,
            source=self.source,
            category=NewsCategory.TW_STOCK,
            stock_codes=stock_codes,
        )
