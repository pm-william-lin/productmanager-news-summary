# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

每日文章摘要腳本：自動抓取產品管理相關網站的最新文章，產出 Markdown 摘要檔。

## Commands

```bash
pip3 install -r requirements.txt   # 安裝依賴
python3 fetch_articles.py          # 執行（含前置檢查）
python3 test_fetch.py              # 單獨跑測試
```

## Architecture

兩種抓取方式：
- **RSS feeds** (`feedparser`): Lenny's Newsletter, SVPG, Intercom Blog, Andrew Chen — 統一由 `fetch_recent_articles()` 處理，來源定義在 `RSS_FEEDS` dict
- **HTML 爬蟲** (`requests` + `BeautifulSoup`): Mind the Product — 專屬函式 `scrape_mindtheproduct()`，因該站無標準 RSS，從首頁 HTML 解析日期（`FEB 19` 格式）和文章連結

所有來源回傳統一格式 `{"title", "link", "date"}`，由 `build_markdown()` 組合成 Markdown 表格。

`fetch_articles.py` 執行時會先呼叫 `run_preflight_checks()` 以 subprocess 跑 `test_fetch.py`，全部通過才繼續。

## Output

輸出至 `output/digest_YYYY-MM-DD.md`，同時印到終端。

## Adding a New Source

- 有 RSS feed：加到 `RSS_FEEDS` dict 即可，現有邏輯自動處理
- 無 RSS feed：需寫專屬爬蟲函式，在 `main()` 中呼叫，並在 `test_fetch.py` 加對應測試
- **Substack 來源注意**：Substack RSS feed 在 GitHub Actions 的雲端 IP 會被擋。目前 Andrew Chen 就有此問題（本地正常，CI 上被擋）。若新增的來源也是 Substack，需提醒使用者考慮 proxy 方案（付費 proxy 服務、RSS bridge、或自架 proxy）

## Planned but Not Yet Implemented

- First Round Review、Reforge Blog（預計透過電子報方式整合）