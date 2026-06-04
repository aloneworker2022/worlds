from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tw_finance_news.models import NewsArticle, NewsCategory, NewsSource


def make_article(**kwargs) -> NewsArticle:
    defaults = dict(
        article_id="test:1",
        title="測試新聞",
        url="https://example.com/news/1",
        published_at=datetime(2025, 6, 4, 10, 0, tzinfo=timezone.utc),
        source=NewsSource.CNYES,
    )
    return NewsArticle(**{**defaults, **kwargs})


def test_stock_codes_deduped_and_sorted():
    article = make_article(stock_codes=["2317", "2330", "2317"])
    assert article.stock_codes == ["2317", "2330"]


def test_stock_codes_empty_by_default():
    article = make_article()
    assert article.stock_codes == []


def test_article_is_immutable():
    article = make_article()
    with pytest.raises(ValidationError):
        article.title = "changed"


def test_article_id_unique_per_source():
    a1 = make_article(article_id="cnyes:1", source=NewsSource.CNYES)
    a2 = make_article(article_id="udn:1", source=NewsSource.UDN)
    assert a1.article_id != a2.article_id


def test_default_category():
    article = make_article()
    assert article.category == NewsCategory.GENERAL
