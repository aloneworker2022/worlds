import pytest
import respx
import httpx

from tw_finance_news.scrapers.statementdog import StatementDogScraper
from tw_finance_news.models import NewsSource


@respx.mock
@pytest.mark.asyncio
async def test_fetch_page_returns_articles(statementdog_html):
    respx.get("https://statementdog.com/news").mock(
        return_value=httpx.Response(200, text=statementdog_html, headers={"content-type": "text/html"})
    )
    scraper = StatementDogScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1)

    assert result.source == NewsSource.STATEMENTDOG
    assert len(result.articles) == 2
    assert result.has_more is True


@respx.mock
@pytest.mark.asyncio
async def test_article_fields(statementdog_html):
    respx.get("https://statementdog.com/news").mock(
        return_value=httpx.Response(200, text=statementdog_html, headers={"content-type": "text/html"})
    )
    scraper = StatementDogScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1)

    article = result.articles[0]
    assert article.article_id == "statementdog:16654"
    assert "台積電" in article.title
    assert article.url == "https://statementdog.com/news/16654"


@respx.mock
@pytest.mark.asyncio
async def test_date_parsing(statementdog_html):
    respx.get("https://statementdog.com/news").mock(
        return_value=httpx.Response(200, text=statementdog_html, headers={"content-type": "text/html"})
    )
    scraper = StatementDogScraper()
    async with scraper:
        result = await scraper._fetch_page(page=1)

    assert result.articles[0].published_at.year == 2025
    assert result.articles[0].published_at.month == 6
    assert result.articles[0].published_at.day == 4


@respx.mock
@pytest.mark.asyncio
async def test_page_3_returns_empty(statementdog_html):
    scraper = StatementDogScraper()
    async with scraper:
        result = await scraper._fetch_page(page=3)

    assert result.articles == []
    assert result.has_more is False
