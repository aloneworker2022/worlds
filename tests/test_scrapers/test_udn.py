import pytest
import respx
import httpx

from tw_finance_news.scrapers.udn import UdnScraper, UDN_RSS_URLS
from tw_finance_news.models import NewsSource


@respx.mock
@pytest.mark.asyncio
async def test_fetch_page_returns_articles(udn_rss):
    respx.get(UDN_RSS_URLS["tw_stock"]).mock(
        return_value=httpx.Response(200, text=udn_rss, headers={"content-type": "application/xml"})
    )
    scraper = UdnScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1)

    assert result.source == NewsSource.UDN
    assert len(result.articles) == 2
    assert result.has_more is False


@respx.mock
@pytest.mark.asyncio
async def test_stock_code_extracted_from_title(udn_rss):
    respx.get(UDN_RSS_URLS["tw_stock"]).mock(
        return_value=httpx.Response(200, text=udn_rss, headers={"content-type": "application/xml"})
    )
    scraper = UdnScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1)

    assert "2330" in result.articles[0].stock_codes
    assert "2317" in result.articles[1].stock_codes


@respx.mock
@pytest.mark.asyncio
async def test_page_2_returns_empty(udn_rss):
    scraper = UdnScraper()
    async with scraper:
        result = await scraper._fetch_page(page=2)

    assert result.articles == []
    assert result.has_more is False


@respx.mock
@pytest.mark.asyncio
async def test_stock_code_filter(udn_rss):
    respx.get(UDN_RSS_URLS["tw_stock"]).mock(
        return_value=httpx.Response(200, text=udn_rss, headers={"content-type": "application/xml"})
    )
    scraper = UdnScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1, stock_code="2330")

    assert all("2330" in a.stock_codes for a in result.articles)
