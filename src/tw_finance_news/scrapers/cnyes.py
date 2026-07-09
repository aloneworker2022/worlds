"""鉅亨網新聞爬蟲 - 使用官方 JSON API"""
from __future__ import annotations

from datetime import datetime

from ..base import BaseScraper
from ..models import NewsArticle, NewsCategory, NewsSource, ScrapeResult
from ..utils import clean_html, extract_stock_codes, unix_to_datetime


class CnyesScraper(BaseScraper):
    """
    鉅亨網 (cnyes.com) 新聞爬蟲

    使用 api.cnyes.com JSON API，支援：
    - 依分類列表：tw_stock、forex、fund 等
    - 依股票代碼搜尋
    - 依日期區間查詢（startAt / endAt，唯一支援伺服器端歷史查詢的來源）
    """

    source = NewsSource.CNYES
    _base_url = "https://api.cnyes.com/media/api/v1"
    _delay_seconds = 0.5

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
        if stock_code:
            url = f"{self._base_url}/search"
            params: dict = {"q": stock_code, "limit": limit, "page": page}
        else:
            cat = category or "tw_stock"
            url = f"{self._base_url}/newslist/category/{cat}"
            params = {"limit": limit, "page": page}

        if start_at is not None:
            params["startAt"] = int(start_at.timestamp())
        if end_at is not None:
            params["endAt"] = int(end_at.timestamp())

        resp = await self._get(url, params=params)
        data = resp.json()
        items_data = data["items"]
        articles = [self._parse_item(item) for item in items_data["data"]]

        return ScrapeResult(
            articles=articles,
            total=items_data.get("total"),
            page=page,
            has_more=page < items_data.get("last_page", 1),
            source=self.source,
        )

    def _parse_item(self, item: dict) -> NewsArticle:
        # 歷史新聞的 summary / keyword / market 等欄位可能為 null，需防呆
        market = item.get("market") or []
        combined_text = " ".join([
            item.get("title") or "",
            item.get("summary") or "",
            " ".join(m.get("code") or "" for m in market),
            " ".join(item.get("otherProduct") or []),
        ])
        stock_codes = extract_stock_codes(combined_text)
        # market 欄位最可靠，直接加入
        for m in market:
            code = m.get("code") or ""
            if code and code not in stock_codes:
                stock_codes.append(code)

        cover: str | None = None
        cover_src = item.get("coverSrc", {})
        if isinstance(cover_src, dict):
            cover = (cover_src.get("m") or cover_src.get("s") or {}).get("src")

        return NewsArticle(
            article_id=f"cnyes:{item['newsId']}",
            title=item["title"],
            summary=item.get("summary") or "",
            content=clean_html(item.get("content") or ""),
            url=f"https://news.cnyes.com/news/id/{item['newsId']}",
            published_at=unix_to_datetime(item["publishAt"]),
            source=self.source,
            category=NewsCategory.TW_STOCK,
            stock_codes=stock_codes,
            tags=item.get("keyword") or [],
            cover_image_url=cover,
        )
