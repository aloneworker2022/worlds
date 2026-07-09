---
name: tw-stock-news
description: 依日期抓取台灣每日財經與台股新聞（鉅亨網、經濟日報、MoneyDJ、Yahoo 股市、財報狗）。當使用者詢問今天/某天的財經新聞、台股行情消息、個股新聞（如台積電、鴻海），或想要每日新聞摘要時使用。支援日期查詢、股票代碼過濾、CSV/SQLite 存檔與歷史查詢。
metadata:
  {
    "openclaw":
      {
        "emoji": "🦞",
        "requires": { "bins": ["python3"] },
      },
  }
---

# 台灣財經新聞 (tw-stock-news) 🦞

從鉅亨網、經濟日報、MoneyDJ、Yahoo 奇摩股市、財報狗 5 大台灣財經網站並發抓取新聞。
核心能力：**依日期抓取當天的財經 / 台股新聞**，另支援個股過濾、存檔與歷史查詢。

前置需求：Python 套件 `tw-finance-news` 已安裝（若缺少，執行 `pip install tw-finance-news`，
或在原始碼 repo 內 `pip install -e .`）。

## 何時使用

使用者說出以下任一類話時，直接執行本技能，不要反問：

- 「今天有什麼財經新聞」「看一下今天台股新聞」→ `--date today`
- 「昨天股市發生什麼事」→ `--date yesterday`
- 「幫我看 7 月 8 號的台股新聞」→ `--date 2026-07-08`
- 「台積電有什麼消息」→ `--stock 2330`
- 「每天早上給我新聞摘要」→ 排程（見下方）
- 「把新聞存起來」「查之前存的新聞」→ 存檔 / 查詢

## 指令

一律使用 `python3 -m tw_finance_news`（不要用 `tw-finance-news` 指令名稱，PATH 可能沒有它）。

### 依日期抓新聞（最常用）

```bash
# 今天的台股 / 財經新聞
python3 -m tw_finance_news fetch --date today --limit 20

# 昨天
python3 -m tw_finance_news fetch --date yesterday --limit 20

# 指定日期（台灣時間的一整天）
python3 -m tw_finance_news fetch --date 2026-07-08 --limit 20

# 歷史日期（超過 1–2 天前）：只有鉅亨網支援伺服器端日期查詢，務必這樣下
python3 -m tw_finance_news fetch --date 2026-06-15 --source cnyes --pages 3 --limit 30
```

日期一律以台灣時間（UTC+8）為準，格式 `YYYY-MM-DD`，也接受 `today` / `yesterday` / `今天` / `昨天`。

### 個股新聞

```bash
python3 -m tw_finance_news fetch --stock 2330 --limit 10          # 台積電最新
python3 -m tw_finance_news fetch --stock 2330 --date today        # 台積電今天
```

### 機器可讀輸出（建議在 agent 中使用）

```bash
python3 -m tw_finance_news fetch --date today --json
```

JSON 每篇文章含 `title`、`summary`、`url`、`published_at`（UTC）、`source`、`stock_codes`、`tags`。

### 存檔與歷史查詢

```bash
python3 -m tw_finance_news fetch --date today --save ~/news.db    # 存 SQLite（自動去重）
python3 -m tw_finance_news query ~/news.db --days 7               # 查最近 7 天
python3 -m tw_finance_news query ~/news.db --stock 2330           # 查個股
```

### 其他

```bash
python3 -m tw_finance_news sources    # 列出可用來源
```

## 結果呈現方式

1. 用繁體中文摘要當天重點（2–3 句）。
2. 列出 5–10 則標題，每則附來源與連結。
3. 個股查詢時，把該股票的新聞排在最前面。
4. 若有明顯市場主軸（如「AI 供應鏈」「降息預期」），一併點出。
5. `--date` 查無結果時，向使用者說明並改用 `--source cnyes --pages 3` 重試一次。

## 每日新聞摘要排程

使用者要「每天固定收新聞」時，建立一個 cron 排程（例如每個交易日早上 8:30 台灣時間），
內容為：執行 `python3 -m tw_finance_news fetch --date today --json`，摘要後推送給使用者，
並可加 `--save ~/news.db` 累積歷史資料。

## 常見台股代碼對照

| 代碼 | 公司 | 代碼 | 公司 |
|------|------|------|------|
| 2330 | 台積電 | 2882 | 國泰金 |
| 2317 | 鴻海 | 2603 | 長榮 |
| 2454 | 聯發科 | 3008 | 大立光 |
| 2308 | 台達電 | 6505 | 台塑化 |
| 2412 | 中華電 | 2002 | 中鋼 |

其他公司名稱請自行換算為 4 位數股票代碼再帶入 `--stock`。

## 注意事項

- RSS 來源（udn / moneydj / yahoo）只有「最新」20–50 篇，無法翻歷史；歷史日期靠鉅亨網 (`cnyes`)。
- 單一來源失敗不影響其他來源，結果仍會回傳。
- 執行頻率建議不超過每 5 分鐘一次，避免對來源網站造成負擔。
- 工商時報 (ctee.com.tw) 有 Cloudflare 防護，不支援。
