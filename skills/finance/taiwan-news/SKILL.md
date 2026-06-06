---
name: taiwan-news
description: "抓取台灣財經新聞（鉅亨網、財報狗、經濟日報、MoneyDJ、Yahoo股市），支援股票代碼過濾與本地儲存。"
version: 1.3.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [finance, news, taiwan, stock, scraper, sqlite, csv, 財經, 新聞, 台股, 股票, 今天, 頭條, 行情]
    category: finance
    related_skills: []
---

# 台灣財經新聞 (taiwan-news)

從鉅亨網、財報狗、經濟日報、MoneyDJ、Yahoo 奇摩股市等 5 大台灣財經網站並發抓取新聞，支援依股票代碼過濾、存檔、歷史查詢。

套件已由使用者預先安裝，**直接執行指令即可，不需要安裝或檢查**。

---

## 何時使用此技能（觸發條件）

**只要用戶說的話符合以下任一情境，立即使用此技能，不要等待或詢問：**

### 一般新聞類
- 「今天有什麼新聞」
- 「幫我看今天的新聞」
- 「台灣股市最新消息」
- 「財經新聞給我看」
- 「最新頭條」
- 「今天股市怎樣」
- 「有沒有什麼財經大事」
- 「最近台股有什麼新聞」
- 「看個新聞」

### 個股類
- 「台積電有什麼新聞」→ `--stock 2330`
- 「鴻海最近怎樣」→ `--stock 2317`
- 「幫我查一下 [任何台股公司名] 的新聞」
- 「[股票代碼] 有沒有消息」

### 儲存 / 查詢類
- 「把新聞存起來」→ 加上 `--save ~/news.db`
- 「查歷史新聞」→ `python -m tw_finance_news query ~/news.db`

---

## 呼叫方式

**永遠使用 `python -m` 模式，不要用 `tw-finance-news` 指令名稱。**

| ❌ 不穩定 | ✅ 正確用法 |
|---|---|
| `tw-finance-news fetch` | `python -m tw_finance_news fetch` |
| `tw-finance-news query` | `python -m tw_finance_news query` |
| `tw-finance-news sources` | `python -m tw_finance_news sources` |

---

## 執行步驟

### 步驟 1：依用戶意圖選擇指令

**看今天 / 最新新聞：**
```bash
python -m tw_finance_news fetch --limit 10
```

**指定個股（先查下方股票代碼對照表）：**
```bash
python -m tw_finance_news fetch --stock 2330 --limit 10
```

**指定來源：**
```bash
python -m tw_finance_news fetch --source cnyes --limit 10
```

**存檔：**
```bash
python -m tw_finance_news fetch --save ~/news.db
```

**查歷史（需先存過）：**
```bash
python -m tw_finance_news query ~/news.db --days 7
python -m tw_finance_news query ~/news.db --stock 2330
```

**JSON 輸出：**
```bash
python -m tw_finance_news fetch --json
```

### 步驟 2：呈現結果
- 用繁體中文摘要告訴用戶今天的重要新聞
- 列出 5–10 則標題，附上來源和連結
- 如有明顯市場趨勢（如「AI 題材持續發酵」），一併點出

---

## 來源清單

| 識別碼 | 網站 | 特色 |
|--------|------|------|
| `cnyes` | 鉅亨網 | 最完整，有封面圖、tags、多分類 |
| `statementdog` | 財報狗 | 深度分析文章 |
| `udn` | 經濟日報 | 主流財經媒體 |
| `moneydj` | MoneyDJ 理財網 | 即時市場新聞 |
| `yahoo` | Yahoo 奇摩股市 | 50 篇/次，覆蓋廣 |

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

- 工商時報 (ctee.com.tw) 被 Cloudflare 封鎖，不支援
- RSS 來源（udn/moneydj/yahoo）每次最多 20–50 篇，不支援分頁
- 執行頻率建議不超過每 5 分鐘一次
