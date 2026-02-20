import feedparser
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from time import mktime

RSS_FEEDS = {
    "Lenny's Newsletter": "https://www.lennysnewsletter.com/feed",
    "SVPG": "https://www.svpg.com/feed/",
    "Intercom Blog": "https://www.intercom.com/blog/feed/",
    "Andrew Chen": "https://andrewchen.substack.com/feed",
}

DAYS = 7
MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def fetch_recent_articles(feed_url, days=DAYS):
    """Parse RSS feed and return articles from the last `days` days."""
    feed = feedparser.parse(feed_url)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    articles = []
    for entry in feed.entries:
        published = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
        if published >= cutoff:
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "date": published.strftime("%Y-%m-%d"),
            })
    return articles


def scrape_mindtheproduct(days=DAYS):
    """Scrape Mind the Product homepage for recent articles."""
    resp = requests.get(
        "https://www.mindtheproduct.com",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    today = datetime.now(timezone.utc)
    date_pattern = re.compile(
        r"^(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{1,2}$"
    )

    seen = set()
    articles = []
    for div in soup.find_all("div", string=date_pattern):
        date_text = div.get_text(strip=True)
        match = re.match(r"(\w+)\s+(\d+)", date_text)
        if not match:
            continue
        month = MONTHS[match.group(1)]
        day = int(match.group(2))
        # Infer year: use current year, but if the date is in the future, use last year
        year = today.year
        try:
            pub_date = datetime(year, month, day, tzinfo=timezone.utc)
        except ValueError:
            continue
        if pub_date > today:
            pub_date = pub_date.replace(year=year - 1)
        if pub_date < cutoff:
            continue

        # Walk up to find the nearest <a> with article href
        parent = div
        for _ in range(10):
            parent = parent.parent
            if parent is None:
                break
            link = parent.find("a", href=re.compile(r"^/[a-z]"))
            if link:
                href = link["href"]
                if href in seen:
                    break
                seen.add(href)
                # Extract clean title
                all_text = link.get_text(separator="|", strip=True).split("|")
                candidates = [
                    t for t in all_text
                    if len(t) > 20 and not date_pattern.match(t)
                ]
                title = candidates[0] if candidates else link.get_text(strip=True)
                articles.append({
                    "title": title,
                    "link": "https://www.mindtheproduct.com" + href,
                    "date": pub_date.strftime("%Y-%m-%d"),
                })
                break

    return articles


def build_markdown(all_articles, today):
    """Build markdown string from collected articles."""
    lines = [f"# 文章摘要 - {today}", ""]
    for source, articles in all_articles.items():
        lines.append(f"## {source}")
        if not articles:
            lines.append("最近 7 天沒有新文章。")
            lines.append("")
            continue
        lines.append("| 日期 | 標題 |")
        lines.append("|------|------|")
        for a in articles:
            lines.append(f"| {a['date']} | [{a['title']}]({a['link']}) |")
        lines.append("")
    return "\n".join(lines)


def run_preflight_checks():
    """執行前置檢查，確認所有來源可正常抓取。"""
    import subprocess
    print("執行前置檢查 ...")
    result = subprocess.run(
        ["python3", "test_fetch.py"],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print("前置檢查失敗，中止執行。")
        raise SystemExit(1)
    print()


def main():
    run_preflight_checks()

    today = datetime.now().strftime("%Y-%m-%d")
    all_articles = {}

    # RSS sources
    for source, url in RSS_FEEDS.items():
        print(f"抓取 {source} ...")
        articles = fetch_recent_articles(url)
        all_articles[source] = articles
        print(f"  找到 {len(articles)} 篇最近 {DAYS} 天的文章")

    # Scrape sources
    print("抓取 Mind the Product ...")
    articles = scrape_mindtheproduct()
    all_articles["Mind the Product"] = articles
    print(f"  找到 {len(articles)} 篇最近 {DAYS} 天的文章")

    md = build_markdown(all_articles, today)

    # 印到終端
    print("\n" + md)

    # 寫入檔案
    os.makedirs("output", exist_ok=True)
    output_path = os.path.join("output", f"digest_{today}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\n已寫入 {output_path}")


if __name__ == "__main__":
    main()
