"""測試所有文章來源的抓取功能是否正常。"""

import feedparser
from fetch_articles import (
    RSS_FEEDS,
    fetch_recent_articles,
    scrape_mindtheproduct,
    build_markdown,
)

PASS = "✓"
FAIL = "✗"


def test_rss_feed(name, url):
    """測試 RSS feed 能否連線並解析出文章。"""
    feed = feedparser.parse(url)
    entry_count = len(feed.entries)
    if entry_count == 0:
        return FAIL, f"回傳 0 篇文章（可能連線失敗或 feed 格式錯誤）"

    # 驗證每篇文章都有必要欄位
    for i, entry in enumerate(feed.entries[:3]):
        missing = []
        if not getattr(entry, "title", None):
            missing.append("title")
        if not getattr(entry, "link", None):
            missing.append("link")
        if not getattr(entry, "published_parsed", None):
            missing.append("published_parsed")
        if missing:
            return FAIL, f"第 {i+1} 篇缺少欄位: {', '.join(missing)}"

    # 測試 fetch_recent_articles 不會報錯（用 365 天確保有結果）
    articles = fetch_recent_articles(url, days=365)
    if not articles:
        return PASS, f"連線正常，{entry_count} 篇文章（但近 365 天都沒有新文章）"

    # 驗證回傳格式
    a = articles[0]
    for key in ("title", "link", "date"):
        if key not in a:
            return FAIL, f"fetch_recent_articles 回傳缺少 '{key}' 欄位"

    return PASS, f"連線正常，共 {entry_count} 篇，近 365 天有 {len(articles)} 篇"


def test_mindtheproduct():
    """測試 Mind the Product 網頁爬蟲。"""
    # 用 365 天確保有結果
    articles = scrape_mindtheproduct(days=365)
    if not articles:
        return FAIL, "回傳 0 篇文章（網頁結構可能已改變）"

    # 驗證回傳格式
    for i, a in enumerate(articles[:3]):
        for key in ("title", "link", "date"):
            if key not in a:
                return FAIL, f"第 {i+1} 篇缺少 '{key}' 欄位"
        if not a["link"].startswith("https://"):
            return FAIL, f"第 {i+1} 篇連結格式錯誤: {a['link']}"
        if len(a["date"]) != 10:
            return FAIL, f"第 {i+1} 篇日期格式錯誤: {a['date']}"

    return PASS, f"爬蟲正常，取得 {len(articles)} 篇文章"


def test_build_markdown():
    """測試 Markdown 產出格式。"""
    sample = {
        "Test Source": [
            {"title": "Test Article", "link": "https://example.com", "date": "2026-01-01"},
        ],
        "Empty Source": [],
    }
    md = build_markdown(sample, "2026-01-01")
    checks = [
        ("# 文章摘要" in md, "缺少標題"),
        ("## Test Source" in md, "缺少來源標題"),
        ("[Test Article](https://example.com)" in md, "缺少文章連結"),
        ("最近 7 天沒有新文章" in md, "缺少空來源提示"),
        ("| 日期 | 標題 |" in md, "缺少表格標頭"),
    ]
    for ok, msg in checks:
        if not ok:
            return FAIL, msg
    return PASS, "Markdown 格式正確"


def main():
    print("=" * 60)
    print("文章抓取功能測試")
    print("=" * 60)

    results = []

    # 測試各 RSS feed
    for name, url in RSS_FEEDS.items():
        print(f"\n測試 {name} ...")
        status, msg = test_rss_feed(name, url)
        results.append((name, status, msg))
        print(f"  {status} {msg}")

    # 測試 Mind the Product 爬蟲
    print(f"\n測試 Mind the Product (HTML 爬蟲) ...")
    status, msg = test_mindtheproduct()
    results.append(("Mind the Product", status, msg))
    print(f"  {status} {msg}")

    # 測試 Markdown 產出
    print(f"\n測試 Markdown 產出 ...")
    status, msg = test_build_markdown()
    results.append(("Markdown 產出", status, msg))
    print(f"  {status} {msg}")

    # 總結
    passed = sum(1 for _, s, _ in results if s == PASS)
    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"結果: {passed}/{total} 通過")
    if passed < total:
        print("失敗項目:")
        for name, s, msg in results:
            if s == FAIL:
                print(f"  {FAIL} {name}: {msg}")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    exit(main())
