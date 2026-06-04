from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tw_finance_news.aggregator import NewsAggregator, _SCRAPER_CLASSES
from tw_finance_news.models import NewsArticle, NewsCategory, NewsSource


def make_article(article_id: str, source: NewsSource, ts: int = 1748995200) -> NewsArticle:
    return NewsArticle(
        article_id=article_id,
        title=f"測試新聞 {article_id}",
        url=f"https://example.com/{article_id}",
        published_at=datetime.fromtimestamp(ts, tz=timezone.utc),
        source=source,
        category=NewsCategory.TW_STOCK,
    )


def make_mock_scraper_class(source: NewsSource, articles: list[NewsArticle]):
    """Return a mock class whose instances have source and get_news_async set."""
    instance = MagicMock()
    instance.source = source
    instance.get_news_async = AsyncMock(return_value=articles)
    cls = MagicMock(return_value=instance)
    return cls


@pytest.mark.asyncio
async def test_aggregator_merges_sources():
    mock_classes = {
        NewsSource.CNYES: make_mock_scraper_class(
            NewsSource.CNYES, [make_article("cnyes:1", NewsSource.CNYES, 1748995200)]
        ),
        NewsSource.UDN: make_mock_scraper_class(
            NewsSource.UDN, [make_article("udn:1", NewsSource.UDN, 1748991600)]
        ),
        NewsSource.MONEYDJ: make_mock_scraper_class(NewsSource.MONEYDJ, []),
        NewsSource.YAHOO: make_mock_scraper_class(NewsSource.YAHOO, []),
        NewsSource.STATEMENTDOG: make_mock_scraper_class(NewsSource.STATEMENTDOG, []),
    }

    with patch.dict("tw_finance_news.aggregator._SCRAPER_CLASSES", mock_classes):
        agg = NewsAggregator()
        results = await agg.get_news_async()

    assert len(results) == 2
    assert results[0].article_id == "cnyes:1"   # newer
    assert results[1].article_id == "udn:1"


@pytest.mark.asyncio
async def test_aggregator_deduplicates():
    dupe = make_article("cnyes:1", NewsSource.CNYES)
    mock_classes = {
        NewsSource.CNYES: make_mock_scraper_class(NewsSource.CNYES, [dupe, dupe]),
        NewsSource.UDN: make_mock_scraper_class(NewsSource.UDN, []),
        NewsSource.MONEYDJ: make_mock_scraper_class(NewsSource.MONEYDJ, []),
        NewsSource.YAHOO: make_mock_scraper_class(NewsSource.YAHOO, []),
        NewsSource.STATEMENTDOG: make_mock_scraper_class(NewsSource.STATEMENTDOG, []),
    }

    with patch.dict("tw_finance_news.aggregator._SCRAPER_CLASSES", mock_classes):
        agg = NewsAggregator()
        results = await agg.get_news_async(deduplicate=True)

    assert len(results) == 1


@pytest.mark.asyncio
async def test_aggregator_tolerates_source_failure():
    good_article = make_article("udn:1", NewsSource.UDN)

    failing_instance = MagicMock()
    failing_instance.source = NewsSource.CNYES
    failing_instance.get_news_async = AsyncMock(side_effect=Exception("Connection error"))
    failing_cls = MagicMock(return_value=failing_instance)

    mock_classes = {
        NewsSource.CNYES: failing_cls,
        NewsSource.UDN: make_mock_scraper_class(NewsSource.UDN, [good_article]),
        NewsSource.MONEYDJ: make_mock_scraper_class(NewsSource.MONEYDJ, []),
        NewsSource.YAHOO: make_mock_scraper_class(NewsSource.YAHOO, []),
        NewsSource.STATEMENTDOG: make_mock_scraper_class(NewsSource.STATEMENTDOG, []),
    }

    with patch.dict("tw_finance_news.aggregator._SCRAPER_CLASSES", mock_classes):
        agg = NewsAggregator()
        results = await agg.get_news_async()

    assert len(results) == 1
    assert results[0].article_id == "udn:1"


@pytest.mark.asyncio
async def test_aggregator_filter_by_source():
    mock_classes = {
        NewsSource.CNYES: make_mock_scraper_class(
            NewsSource.CNYES, [make_article("cnyes:1", NewsSource.CNYES)]
        ),
        NewsSource.UDN: make_mock_scraper_class(
            NewsSource.UDN, [make_article("udn:1", NewsSource.UDN)]
        ),
        NewsSource.MONEYDJ: make_mock_scraper_class(NewsSource.MONEYDJ, []),
        NewsSource.YAHOO: make_mock_scraper_class(NewsSource.YAHOO, []),
        NewsSource.STATEMENTDOG: make_mock_scraper_class(NewsSource.STATEMENTDOG, []),
    }

    with patch.dict("tw_finance_news.aggregator._SCRAPER_CLASSES", mock_classes):
        agg = NewsAggregator(sources=[NewsSource.CNYES])
        results = await agg.get_news_async()

    assert len(results) == 1
    assert results[0].source == NewsSource.CNYES
