# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

每日自動抓取產品管理相關網站的最新文章，用 Claude API 產生中文摘要，發送到 LINE 群組。

## Architecture

### 執行方式

全部由 **n8n workflow** 處理（不再使用 GitHub Actions）。

- n8n instance: `https://pm-williamlin-n8n.zeabur.app`
- Workflow: `PM Daily Digest` (ID: `idvoV9PdCjtZPgJw`)
- 排程: 每天台灣時間 09:00 自動執行
- 手動測試: GET `https://pm-williamlin-n8n.zeabur.app/webhook-test/pm-digest`

### Pipeline（10 nodes）

```
Schedule Trigger (9AM Taipei) ──┐
                                ├→ Source Config → Fetch RSS → Parse & Filter RSS
Webhook Test ───────────────────┘        ↓
                               Fetch Content → Prepare Claude → Claude Summarize
                                        ↓
                               Build LINE Message → Send LINE
```

### 文章來源

| 來源 | 備註 |
|------|------|
| Lenny's Newsletter | Substack |
| SVPG | |
| Intercom Blog | |
| Andrew Chen | Substack |
| Stratechery | Ben Thompson，科技產業策略分析，幾乎每天更新 |
| The Pragmatic Engineer | Gergely Orosz，工程管理 + 產品視角 |
| Casey Winters | Substack，前 Grubhub/Pinterest，增長策略 |
| Nikitha | Substack，PM / AI 基礎設施 / 新創 |

所有來源都是 RSS，定義在 n8n `Source Config` Code node 中。

### AI 摘要

- 透過 HTTP Request 直接呼叫 Anthropic Messages API（claude-sonnet-4-5-20250929）
- 先抓取文章正文（截斷至 5000 字元）
- API 失敗時跳過該篇摘要，不中斷 pipeline

### LINE 通知

- 使用 LINE Messaging API push message
- 訊息超過 5000 字元會自動截斷
- Bot: 產品經理的百憂解

## Adding a New RSS Source

在 n8n workflow 的 `Source Config` Code node 中，加一行到 `sources` array：

```javascript
["來源名稱", "https://example.com/feed"]
```

也需要在 `Build LINE Message` Code node 的 `sourceOrder` array 中加入同名字串以控制顯示順序。

**Substack 來源**：n8n (Zeabur) 的 IP 不會被 Substack 擋，可以直接加。

## Legacy Files（保留但不再使用）

- `fetch_articles.py` — 原本的 Python pipeline（已遷移到 n8n）
- `test_fetch.py` — 原本的測試（n8n 版本不需要）
- `requirements.txt` — Python 依賴
- `.env` — 環境變數（credentials 已存在 n8n 中）

## Planned but Not Yet Implemented

- Mind the Product（HTML 爬蟲，需要在 n8n Code node 中實作）
- First Round Review、Reforge Blog（預計透過電子報方式整合）
