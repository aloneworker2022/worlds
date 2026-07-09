"""CLI: tw-finance-news"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .aggregator import NewsAggregator
from .models import NewsSource
from .storage import CsvStorage, SqliteStorage
from .utils import TAIPEI_TZ

app = typer.Typer(
    name="tw-finance-news",
    help="台灣財經新聞爬蟲 - 抓取各大財經網站最新新聞",
    no_args_is_help=True,
)
console = Console()


def _parse_date(value: Optional[str]) -> dt.date | None:
    if not value:
        return None
    v = value.strip().lower()
    today = dt.datetime.now(TAIPEI_TZ).date()
    if v in ("today", "今天"):
        return today
    if v in ("yesterday", "昨天"):
        return today - dt.timedelta(days=1)
    try:
        return dt.date.fromisoformat(v)
    except ValueError as e:
        raise typer.BadParameter(
            "日期格式需為 YYYY-MM-DD，或 today / yesterday / 今天 / 昨天"
        ) from e


def _parse_sources(sources: Optional[str]) -> list[NewsSource] | None:
    if not sources:
        return None
    try:
        return [NewsSource(s.strip()) for s in sources.split(",")]
    except ValueError as e:
        raise typer.BadParameter(f"無效的來源名稱: {e}") from e


def _print_table(articles: list, title: str) -> None:
    table = Table(title=title, show_lines=True, expand=True)
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


@app.command("fetch")
def fetch(
    stock: Optional[str] = typer.Option(None, "--stock", "-s", help="依股票代碼過濾，例如 2330"),
    source: Optional[str] = typer.Option(
        None, "--source", help=f"指定來源（逗號分隔）: {', '.join(s.value for s in NewsSource)}"
    ),
    date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="只抓指定日期（台灣時間）的新聞：YYYY-MM-DD 或 today / yesterday。歷史日期建議搭配 --source cnyes --pages 3",
    ),
    pages: int = typer.Option(1, "--pages", "-p", help="每個來源抓取的頁數"),
    limit: int = typer.Option(20, "--limit", "-l", help="每個來源每頁的文章數"),
    save: Optional[str] = typer.Option(None, "--save", help="儲存到檔案（.csv 或 .db/.sqlite）"),
    json_output: bool = typer.Option(False, "--json", "-j", help="以 JSON 格式輸出"),
):
    """抓取並顯示台灣財經新聞。"""
    srcs = _parse_sources(source)
    target_date = _parse_date(date)
    aggregator = NewsAggregator(sources=srcs)

    desc = []
    if stock:
        desc.append(f"股票 {stock}")
    if target_date:
        desc.append(f"日期 {target_date.isoformat()}")
    status_msg = f"正在抓取新聞{'（' + '、'.join(desc) + '）' if desc else ''}..."
    with console.status(status_msg):
        articles = aggregator.get_news(
            stock_code=stock,
            pages=pages,
            limit_per_source=limit,
            date=target_date,
        )

    if not articles:
        console.print("[yellow]沒有找到符合條件的新聞。[/yellow]")
        if target_date:
            console.print(
                "[dim]提示：RSS 來源只有最新新聞，歷史日期請改用 "
                "--source cnyes --pages 3 --limit 30[/dim]"
            )
        raise typer.Exit(0)

    if save:
        path = Path(save)
        suffix = path.suffix.lower()
        if suffix == ".csv":
            storage = CsvStorage(path)
            added = storage.save(articles)
            console.print(f"[green]已儲存到 {path}（新增 {added} 篇）[/green]")
        elif suffix in (".db", ".sqlite", ".sqlite3"):
            storage = SqliteStorage(path)
            added = storage.save(articles)
            console.print(f"[green]已儲存到 {path}（新增 {added} 篇，共 {storage.count()} 篇）[/green]")
        else:
            raise typer.BadParameter("儲存格式需為 .csv 或 .db / .sqlite", param_hint="--save")

    if json_output:
        # 用 typer.echo 而非 console.print：rich 會依終端寬度換行，破壞 JSON
        typer.echo(
            json.dumps(
                [a.model_dump(mode="json") for a in articles],
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    _print_table(articles, f"台灣財經新聞（共 {len(articles)} 篇）")


@app.command("query")
def query(
    db_path: str = typer.Argument(..., help="SQLite 資料庫路徑，例如 news.db"),
    stock: Optional[str] = typer.Option(None, "--stock", "-s", help="依股票代碼過濾"),
    source: Optional[str] = typer.Option(None, "--source", help="依來源過濾"),
    days: Optional[int] = typer.Option(None, "--days", "-d", help="只顯示最近 N 天"),
    json_output: bool = typer.Option(False, "--json", "-j", help="以 JSON 格式輸出"),
):
    """查詢已儲存在 SQLite 資料庫的新聞。"""
    path = Path(db_path)
    if not path.exists():
        console.print(f"[red]找不到資料庫：{path}[/red]")
        raise typer.Exit(1)

    db = SqliteStorage(path)
    articles = db.load(stock_code=stock, source=source, days=days)

    if not articles:
        console.print("[yellow]沒有符合條件的記錄。[/yellow]")
        raise typer.Exit(0)

    if json_output:
        # 用 typer.echo 而非 console.print：rich 會依終端寬度換行，破壞 JSON
        typer.echo(
            json.dumps(
                [a.model_dump(mode="json") for a in articles],
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    filter_desc = []
    if stock:
        filter_desc.append(f"股票={stock}")
    if source:
        filter_desc.append(f"來源={source}")
    if days:
        filter_desc.append(f"最近{days}天")
    title = f"查詢結果（{len(articles)} 篇）" + (f" [{', '.join(filter_desc)}]" if filter_desc else "")

    _print_table(articles, title)
    console.print(f"[dim]資料庫共 {db.count()} 篇[/dim]")


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
