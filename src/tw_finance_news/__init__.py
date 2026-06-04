"""台灣財經新聞爬蟲套件"""
from .aggregator import NewsAggregator
from .models import NewsArticle, NewsCategory, NewsSource
from .scrapers.cnyes import CnyesScraper
from .scrapers.moneydj import MoneyDJScraper
from .scrapers.statementdog import StatementDogScraper
from .scrapers.udn import UdnScraper
from .scrapers.yahoo import YahooFinanceScraper

__version__ = "0.1.0"
__all__ = [
    "NewsAggregator",
    "NewsArticle",
    "NewsSource",
    "NewsCategory",
    "CnyesScraper",
    "UdnScraper",
    "MoneyDJScraper",
    "YahooFinanceScraper",
    "StatementDogScraper",
]
