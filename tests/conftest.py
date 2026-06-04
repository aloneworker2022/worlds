import json
import pathlib

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def cnyes_response() -> dict:
    return json.loads((FIXTURES_DIR / "cnyes_tw_stock.json").read_text())


@pytest.fixture
def udn_rss() -> str:
    return (FIXTURES_DIR / "udn_stock.xml").read_text()


@pytest.fixture
def moneydj_rss() -> str:
    return (FIXTURES_DIR / "moneydj_stock.xml").read_text()


@pytest.fixture
def yahoo_rss() -> str:
    return (FIXTURES_DIR / "yahoo_stock.xml").read_text()


@pytest.fixture
def statementdog_html() -> str:
    return (FIXTURES_DIR / "statementdog_news.html").read_text()
