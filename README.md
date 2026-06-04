# tw-finance-news

台灣財經新聞爬蟲套件，支援鉅亨網、財報狗、經濟日報、MoneyDJ、Yahoo奇摩股市等主要財經網站。

## 安裝

```bash
pip install tw-finance-news
```

## 快速開始

```python
from tw_finance_news import NewsAggregator, NewsSource

# 抓取所有來源的最新新聞
agg = NewsAggregator()
articles = agg.get_news()

for article in articles[:5]:
    print(f"[{article.source}] {article.title}")
    print(f"  {article.url}")

# 依股票代碼過濾（台積電 2330）
articles = agg.get_news(stock_code="2330")

# 只使用特定來源
agg = NewsAggregator(sources=[NewsSource.CNYES, NewsSource.UDN])
articles = agg.get_news()
```

## 支援的新聞來源

| 來源 | 識別碼 | 方法 | 特色 |
|------|--------|------|------|
| 鉅亨網 | `cnyes` | JSON API | 最完整，支援股票代碼搜尋 |
| 經濟日報 | `udn` | RSS | 每次 20 篇 |
| MoneyDJ 理財網 | `moneydj` | RSS | 每次 20 篇 |
| Yahoo 奇摩股市 | `yahoo` | RSS | 每次 50 篇 |
| 財報狗 | `statementdog` | HTML 爬取 | 台股分析專業網站 |

## CLI 使用

```bash
# 抓取最新新聞
tw-finance-news fetch

# 依股票代碼過濾
tw-finance-news fetch --stock 2330

# 指定來源
tw-finance-news fetch --source cnyes,udn

# JSON 輸出
tw-finance-news fetch --json

# 列出所有可用來源
tw-finance-news sources
```

## 非同步使用

```python
import asyncio
from tw_finance_news import NewsAggregator

async def main():
    agg = NewsAggregator()
    articles = await agg.get_news_async(stock_code="2330")
    return articles

articles = asyncio.run(main())
```

## 資料模型

```python
class NewsArticle:
    article_id: str          # 唯一識別碼，如 "cnyes:6484021"
    title: str               # 新聞標題
    summary: str             # 摘要
    content: str             # 全文（部分來源）
    url: str                 # 文章連結
    published_at: datetime   # 發布時間（UTC）
    source: NewsSource       # 來源
    category: NewsCategory   # 分類
    stock_codes: list[str]   # 相關股票代碼，如 ["2330", "2317"]
    tags: list[str]          # 標籤
    cover_image_url: str     # 封面圖片
```
