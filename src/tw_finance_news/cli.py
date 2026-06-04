"""CLI: tw-finance-news"""
from __future__ import annotations

import json
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .aggregator import NewsAggregator
from .models import NewsSource

app = typer.Typer(
    name="tw-finance-news",
    help="台灣財經新聞爬蟲 - 抓取各大財經網站最新新聞",
    no_args_is_help=True,
)
console = Console()


def _parse_sources(sources: Optional[str]) -> list[NewsSource] | None:
    if not sources:
        return None
    try:
        return [NewsSource(s.strip()) for s in sources.split(",")]
    except ValueError as e:
        raise typer.BadParameter(f"無效的來源名稱: {e}") from e


@app.command("fetch")
def fetch(
    stock: Optional[str] = typer.Option(None, "--stock", "-s", help="依股票代碼過濾，例如 2330"),
    source: Optional[str] = typer.Option(
        None, "--source", help=f"指定來源（逗號分隔）: {', '.join(s.value for s in NewsSource)}"
    ),
    pages: int = typer.Option(1, "--pages", "-p", help="每個來源抓取的頁數"),
    limit: int = typer.Option(20, "--limit", "-l", help="每個來源每頁的文章數"),
    json_output: bool = typer.Option(False, "--json", "-j", help="以 JSON 格式輸出"),
):
    """抓取並顯示台灣財經新聞。"""
    srcs = _parse_sources(source)
    aggregator = NewsAggregator(sources=srcs)

    status_msg = f"正在抓取新聞{'（股票 ' + stock + '）' if stock else ''}..."
    with console.status(status_msg):
        articles = aggregator.get_news(
            stock_code=stock,
            pages=pages,
            limit_per_source=limit,
        )

    if not articles:
        console.print("[yellow]沒有找到符合條件的新聞。[/yellow]")
        raise typer.Exit(0)

    if json_output:
        console.print(
            json.dumps(
                [a.model_dump(mode="json") for a in articles],
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    table = Table(
        title=f"台灣財經新聞（共 {len(articles)} 篇）",
        show_lines=True,
        expand=True,
    )
    table.add_column("來源", style="cyan", width=12)
    table.add_column("時間", style="green", width=16)
    table.add_column("標題", ratio=3, overflow="fold")
    table.add_column("股票", style="yellow", width=12)
    table.add_column("連結", ratio=2, overflow="fold")

    for article in articles:
        table.add_row(
            article.source.value,
            article.published_at.strftime("%Y-%m-%d %H:%M"),
            article.title,
            ", ".join(article.stock_codes[:5]),
            article.url,
        )

    console.print(table)


@app.command("sources")
def list_sources():
    """列出所有可用的新聞來源。"""
    descriptions = {
        NewsSource.CNYES: "鉅亨網 - JSON API，支援股票代碼搜尋，資料最完整",
        NewsSource.UDN: "經濟日報 - RSS Feed，每次最多 20 篇",
        NewsSource.MONEYDJ: "MoneyDJ 理財網 - RSS Feed，每次最多 20 篇",
        NewsSource.YAHOO: "Yahoo 奇摩股市 - RSS Feed，每次最多 50 篇",
        NewsSource.STATEMENTDOG: "財報狗 - HTML 爬取，台股分析專業網站",
    }
    console.print("\n[bold]可用的新聞來源：[/bold]\n")
    for src, desc in descriptions.items():
        console.print(f"  [cyan]{src.value:<15}[/cyan] {desc}")
    console.print()
