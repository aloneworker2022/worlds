---
name: taiwan-news
description: "抓取台灣財經新聞（鉅亨網、財報狗、經濟日報、MoneyDJ、Yahoo股市），支援股票代碼過濾與本地儲存。"
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, news, taiwan, stock, scraper, sqlite, csv]
    category: finance
    related_skills: []
---

# 台灣財經新聞 (taiwan-news)

從鉅亨網、財報狗、經濟日報、MoneyDJ、Yahoo 奇摩股市等 5 大台灣財經網站並發抓取新聞，支援依股票代碼過濾、存檔、歷史查詢。

## 安裝

套件來源：`https://github.com/aloneworker2022/worlds`，branch `claude/taiwan-finance-news-scraper-fbuml`

```bash
git clone https://github.com/aloneworker2022/worlds.git -b claude/taiwan-finance-news-scraper-fbuml ~/tw-finance-news-src
pip install ~/tw-finance-news-src
```

安裝後可用 CLI 指令 `tw-finance-news`。

---

## 決策樹

```
用戶問財經新聞？
│
├─ 只是看最新新聞
│   └─ tw-finance-news fetch
│
├─ 指定股票（例：台積電、鴻海、聯發科）
│   ├─ 先確認股票代碼（台積電=2330、鴻海=2317、聯發科=2454）
│   └─ tw-finance-news fetch --stock <代碼>
│
├─ 指定新聞來源
│   └─ tw-finance-news fetch --source cnyes          # 鉅亨網
│   └─ tw-finance-news fetch --source cnyes,udn      # 多個來源
│
├─ 想要存起來（避免重複、累積歷史）
│   ├─ SQLite（推薦，可查詢）
│   │   └─ tw-finance-news fetch --save ~/news.db
│   └─ CSV（簡單格式）
│       └─ tw-finance-news fetch --save ~/news.csv
│
└─ 查詢歷史（需要先 --save 過）
    ├─ 看所有記錄         tw-finance-news query ~/news.db
    ├─ 過濾股票           tw-finance-news query ~/news.db --stock 2330
    ├─ 最近 N 天          tw-finance-news query ~/news.db --days 7
    └─ 指定來源           tw-finance-news query ~/news.db --source cnyes
```

---

## 來源清單

| 識別碼 | 網站 | 方法 | 特色 |
|--------|------|------|------|
| `cnyes` | 鉅亨網 | JSON API | 最完整，有封面圖、tags、多分類 |
| `statementdog` | 財報狗 | HTML | 深度分析文章 |
| `udn` | 經濟日報 | RSS | 主流財經媒體 |
| `moneydj` | MoneyDJ 理財網 | RSS | 即時市場新聞 |
| `yahoo` | Yahoo 奇摩股市 | RSS | 50 篇/次，覆蓋廣 |

---

## CLI 用法

### 抓最新新聞
```bash
tw-finance-news fetch
tw-finance-news fetch --limit 10        # 每個來源限 10 篇
tw-finance-news fetch --pages 2         # 鉅亨網抓 2 頁（其他來源無分頁）
```

### 依股票代碼過濾
```bash
tw-finance-news fetch --stock 2330      # 台積電
tw-finance-news fetch --stock 2317      # 鴻海
tw-finance-news fetch --stock 2454      # 聯發科
tw-finance-news fetch --stock 2330 --source cnyes,udn
```

### 指定來源
```bash
tw-finance-news fetch --source cnyes
tw-finance-news fetch --source cnyes,udn,moneydj
tw-finance-news sources                 # 列出所有可用來源
```

### 儲存到檔案
```bash
# SQLite（推薦，支援查詢過濾）
tw-finance-news fetch --save ~/news.db
tw-finance-news fetch --stock 2330 --save ~/tsmc.db

# CSV
tw-finance-news fetch --save ~/news.csv
```

### 查詢歷史記錄（SQLite）
```bash
tw-finance-news query ~/news.db
tw-finance-news query ~/news.db --stock 2330
tw-finance-news query ~/news.db --days 7
tw-finance-news query ~/news.db --source cnyes
tw-finance-news query ~/news.db --json         # JSON 格式輸出
```

### JSON 輸出（供程式處理）
```bash
tw-finance-news fetch --json
tw-finance-news fetch --stock 2330 --json | python -m json.tool
```

---

## Python API 用法

```python
from tw_finance_news import NewsAggregator, NewsSource, CnyesScraper, SqliteStorage

# 抓所有來源
agg = NewsAggregator()
articles = agg.get_news()

# 依股票代碼過濾
articles = agg.get_news(stock_code="2330")

# 指定來源
agg = NewsAggregator(sources=[NewsSource.CNYES, NewsSource.UDN])
articles = agg.get_news()

# 只用鉅亨網，抓 2 頁
scraper = CnyesScraper()
articles = scraper.get_news(pages=2, stock_code="2330")

# 儲存到 SQLite
db = SqliteStorage("~/news.db")
added = db.save(articles)           # 自動去重，回傳新增筆數
print(f"新增 {added} 篇，共 {db.count()} 篇")

# 查詢
recent = db.load(stock_code="2330", days=7)
```

---

## 資料模型

每篇新聞包含：
- `article_id` — 唯一 ID，格式如 `cnyes:6484021`
- `title` — 標題
- `summary` — 摘要
- `content` — 全文（部分來源）
- `url` — 原文連結
- `published_at` — 發布時間（UTC datetime）
- `source` — 來源（cnyes / udn / moneydj / yahoo / statementdog）
- `stock_codes` — 相關股票代碼清單，如 `["2330", "2317"]`
- `tags` — 標籤（鉅亨網提供）
- `cover_image_url` — 封面圖（鉅亨網提供）

---

## 常見台灣股票代碼

| 代碼 | 公司 |
|------|------|
| 2330 | 台積電 |
| 2317 | 鴻海 |
| 2454 | 聯發科 |
| 2308 | 台達電 |
| 2412 | 中華電 |
| 2882 | 國泰金 |
| 2603 | 長榮 |
| 3008 | 大立光 |
| 6505 | 台塑化 |
| 2002 | 中鋼 |

---

## 注意事項

- 工商時報 (ctee.com.tw) 被 Cloudflare WAF 封鎖，未支援
- RSS 來源（udn/moneydj/yahoo）不支援分頁，每次最多 20–50 篇
- 財報狗 (statementdog) 限 2 頁，HTML 爬取可能因網站改版而失效
- 執行頻率建議不超過每 5 分鐘一次，避免對網站造成壓力
