import json
from datetime import timezone

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
