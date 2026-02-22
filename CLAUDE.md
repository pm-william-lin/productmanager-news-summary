# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

每日自動抓取產品管理相關網站的最新文章，用 Claude API 產生中文摘要，輸出 Markdown 檔並發送到 LINE 群組。

## Commands

```bash
pip3 install -r requirements.txt   # 安裝依賴
python3 fetch_articles.py          # 執行完整流程（前置檢查 → 抓取 → 摘要 → 輸出 → LINE 通知）
python3 test_fetch.py              # 單獨跑測試
```

## Architecture

### 執行流程

```
run_preflight_checks()     # 跑 test_fetch.py，失敗才中斷（RSS 失敗僅警告）
        ↓
抓取文章（RSS + HTML 爬蟲）
        ↓
fetch_article_content()    # 抓取每篇文章正文
        ↓
summarize_article()        # Claude API 產生 3-5 句中文摘要
        ↓
build_markdown()           # 產出 Markdown 檔到 output/
        ↓
build_line_message()       # 格式化為純文字
        ↓
send_line_message()        # 透過 LINE Messaging API 發送到群組
```

### 文章來源

| 來源 | 方法 | 備註 |
|------|------|------|
| Lenny's Newsletter | RSS | Substack，GitHub Actions 上可能被擋 |
| SVPG | RSS | |
| Intercom Blog | RSS | |
| Andrew Chen | RSS | Substack，GitHub Actions 上被擋（僅警告不中斷） |
| Stratechery | RSS | Ben Thompson，科技產業策略分析，幾乎每天更新 |
| The Pragmatic Engineer | RSS | Gergely Orosz，工程管理 + 產品視角，每週 2-3 篇 |
| Casey Winters | RSS | 前 Grubhub/Pinterest，增長策略，Substack，GitHub Actions 上可能被擋 |
| Mind the Product | HTML 爬蟲 | 無標準 RSS，從首頁解析日期（`FEB 19` 格式）和連結 |

- RSS 來源定義在 `RSS_FEEDS` dict，由 `fetch_recent_articles()` 統一處理
- HTML 爬蟲來源各有專屬函式（`scrape_mindtheproduct()`）
- 所有來源回傳統一格式 `{"title", "link", "date", "summary"}`

### AI 摘要

- 使用 `anthropic` SDK 呼叫 Claude Sonnet API
- 先用 `fetch_article_content()` 抓正文（截斷至 5000 字元）
- 無 API key 時自動跳過，不影響其他功能
- API 呼叫失敗時 catch exception，跳過該篇摘要

### LINE 通知

- 使用 LINE Messaging API push message
- 訊息超過 5000 字元會自動截斷
- 無 token 或 group ID 時自動跳過

### 排程

- GitHub Actions：每天台灣時間 09:00（UTC 01:00）自動執行
- 也可手動觸發：GitHub repo → Actions → Daily Article Digest → Run workflow
- Workflow 定義在 `.github/workflows/daily-digest.yml`

### 前置檢查（test_fetch.py）

- RSS feed 連線 + 欄位驗證（失敗為**警告**，不中斷）
- Mind the Product 爬蟲驗證
- 文章正文抓取驗證
- Markdown 輸出格式驗證
- LINE 訊息格式驗證

## Environment Variables（`.env`）

```
ANTHROPIC_API_KEY=        # Claude API key（摘要功能）
LINE_CHANNEL_ACCESS_TOKEN= # LINE Bot token（通知功能）
LINE_GROUP_ID=            # LINE 群組 ID（通知目標）
```

GitHub Actions 上存為 repo secrets，本地用 `.env` 檔（已在 `.gitignore`）。

## Adding a New Source

- 有 RSS feed：加到 `RSS_FEEDS` dict 即可
- 無 RSS feed：寫專屬爬蟲函式，在 `main()` 中呼叫，並在 `test_fetch.py` 加對應測試
- **Substack 來源注意**：GitHub Actions 雲端 IP 會被擋。目前 Andrew Chen 就有此問題。若新增 Substack 來源，需提醒使用者考慮 proxy 方案（付費 proxy、RSS bridge、或自架 proxy）

## Planned but Not Yet Implemented

- First Round Review、Reforge Blog（預計透過電子報方式整合）
