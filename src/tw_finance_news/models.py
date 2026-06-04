from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, field_validator


class NewsSource(StrEnum):
    CNYES = "cnyes"
    UDN = "udn"
    MONEYDJ = "moneydj"
    YAHOO = "yahoo"
    STATEMENTDOG = "statementdog"


class NewsCategory(StrEnum):
    TW_STOCK = "tw_stock"
    FOREX = "forex"
    FUND = "fund"
    ECONOMY = "economy"
    GENERAL = "general"


class NewsArticle(BaseModel):
    article_id: str
    title: str
    summary: str = ""
    content: str = ""
    url: str
    published_at: datetime
    source: NewsSource
    category: NewsCategory = NewsCategory.GENERAL
    stock_codes: list[str] = []
    tags: list[str] = []
    cover_image_url: str | None = None

    @field_validator("stock_codes", mode="before")
    @classmethod
    def dedupe_sort(cls, v: list[str]) -> list[str]:
        return sorted(set(v))

    model_config = {"frozen": True}


class ScrapeResult(BaseModel):
    articles: list[NewsArticle]
    total: int | None = None
    page: int = 1
    has_more: bool = False
    source: NewsSource
