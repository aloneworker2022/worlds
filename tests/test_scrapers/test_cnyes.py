import json
from datetime import datetime, timezone

import pytest
import respx
import httpx

from tw_finance_news.scrapers.cnyes import CnyesScraper
from tw_finance_news.models import NewsSource


@pytest.fixture
def cnyes_data(cnyes_response):
    return cnyes_response


@respx.mock
@pytest.mark.asyncio
async def test_fetch_page_category(cnyes_data):
    respx.get("https://api.cnyes.com/media/api/v1/newslist/category/tw_stock").mock(
        return_value=httpx.Response(200, json=cnyes_data)
    )
    scraper = CnyesScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1)

    assert result.source == NewsSource.CNYES
    assert len(result.articles) == 2
    assert result.articles[0].article_id == "cnyes:6484021"
    assert "2330" in result.articles[0].stock_codes


@respx.mock
@pytest.mark.asyncio
async def test_fetch_page_stock_search(cnyes_data):
    respx.get("https://api.cnyes.com/media/api/v1/search").mock(
        return_value=httpx.Response(200, json=cnyes_data)
    )
    scraper = CnyesScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1, stock_code="2330")

    assert len(result.articles) == 2


@respx.mock
@pytest.mark.asyncio
async def test_fetch_page_date_range_params(cnyes_data):
    route = respx.get("https://api.cnyes.com/media/api/v1/newslist/category/tw_stock").mock(
        return_value=httpx.Response(200, json=cnyes_data)
    )
    start = datetime(2025, 6, 3, 16, 0, 0, tzinfo=timezone.utc)
    end = datetime(2025, 6, 4, 15, 59, 59, tzinfo=timezone.utc)
    scraper = CnyesScraper()
    async with scraper:
        await scraper._fetch_page(page=1, start_at=start, end_at=end)

    params = route.calls.last.request.url.params
    assert params["startAt"] == str(int(start.timestamp()))
    assert params["endAt"] == str(int(end.timestamp()))


@respx.mock
@pytest.mark.asyncio
async def test_get_news_filters_by_date_range(cnyes_data):
    respx.get("https://api.cnyes.com/media/api/v1/newslist/category/tw_stock").mock(
        return_value=httpx.Response(200, json=cnyes_data)
    )
    # fixture 兩篇：publishAt 1748991600 (23:00 UTC) 與 1748995200 (00:00 UTC)
    # 區間只涵蓋後者，前者應被客戶端過濾掉
    start = datetime(2025, 6, 3, 23, 30, 0, tzinfo=timezone.utc)
    scraper = CnyesScraper()
    articles = await scraper.get_news_async(start_at=start)

    assert len(articles) == 1
    assert articles[0].article_id == "cnyes:6484021"


def test_parse_item_tolerates_null_fields(cnyes_data):
    # 歷史新聞 API 常見 summary / keyword / market 等欄位為 null
    item = dict(cnyes_data["items"]["data"][0])
    item.update({
        "summary": None,
        "keyword": None,
        "market": None,
        "otherProduct": None,
        "content": None,
        "coverSrc": None,
    })
    article = CnyesScraper()._parse_item(item)
    assert article.summary == ""
    assert article.content == ""
    assert article.tags == []
    assert article.cover_image_url is None


@respx.mock
@pytest.mark.asyncio
async def test_parse_cover_image(cnyes_data):
    respx.get("https://api.cnyes.com/media/api/v1/newslist/category/tw_stock").mock(
        return_value=httpx.Response(200, json=cnyes_data)
    )
    scraper = CnyesScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1)

    assert result.articles[0].cover_image_url is not None
    assert result.articles[1].cover_image_url is None


@respx.mock
@pytest.mark.asyncio
async def test_content_html_stripped(cnyes_data):
    respx.get("https://api.cnyes.com/media/api/v1/newslist/category/tw_stock").mock(
        return_value=httpx.Response(200, json=cnyes_data)
    )
    scraper = CnyesScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1)

    assert "<p>" not in result.articles[0].content


@respx.mock
@pytest.mark.asyncio
async def test_published_at_utc(cnyes_data):
    respx.get("https://api.cnyes.com/media/api/v1/newslist/category/tw_stock").mock(
        return_value=httpx.Response(200, json=cnyes_data)
    )
    scraper = CnyesScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1)

    assert result.articles[0].published_at.tzinfo == timezone.utc
