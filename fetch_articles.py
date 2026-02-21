import feedparser
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from time import mktime

from dotenv import load_dotenv

load_dotenv()

RSS_FEEDS = {
    "Lenny's Newsletter": "https://www.lennysnewsletter.com/feed",
    "SVPG": "https://www.svpg.com/feed/",
    "Intercom Blog": "https://www.intercom.com/blog/feed/",
    "Andrew Chen": "https://andrewchen.substack.com/feed",
}

DAYS = 1
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
        year = today.year
        try:
            pub_date = datetime(year, month, day, tzinfo=timezone.utc)
        except ValueError:
            continue
        if pub_date > today:
            pub_date = pub_date.replace(year=year - 1)
        if pub_date < cutoff:
            continue

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


# --- AI 摘要 ---

def fetch_article_content(url):
    """抓取文章網頁正文。"""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # 移除不需要的元素
    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # 嘗試找 article 標籤，否則用 body
    article = soup.find("article") or soup.find("body")
    if not article:
        return None

    text = article.get_text(separator="\n", strip=True)
    # 截斷過長的內容（節省 API token）
    return text[:5000] if text else None


def summarize_article(title, content):
    """用 Claude API 產生文章摘要。"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    f"請用繁體中文為以下文章寫 3-5 句摘要，重點摘述文章的核心觀點和關鍵洞見。\n\n"
                    f"文章標題：{title}\n\n"
                    f"文章內容：\n{content}"
                ),
            }],
        )
        return message.content[0].text
    except Exception as e:
        print(f"    AI 摘要失敗: {e}")
        return None


def summarize_all_articles(all_articles):
    """對所有文章產生 AI 摘要。"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  未設定 ANTHROPIC_API_KEY，跳過 AI 摘要")
        return

    total = sum(len(arts) for arts in all_articles.values())
    if total == 0:
        return

    print(f"\n產生 AI 摘要（共 {total} 篇）...")
    count = 0
    for source, articles in all_articles.items():
        for article in articles:
            count += 1
            print(f"  [{count}/{total}] {article['title'][:50]}...")
            content = fetch_article_content(article["link"])
            if content:
                summary = summarize_article(article["title"], content)
                article["summary"] = summary
            else:
                article["summary"] = None


# --- Markdown 產出 ---

def build_markdown(all_articles, today):
    """Build markdown string from collected articles."""
    lines = [f"# 文章摘要 - {today}", ""]
    for source, articles in all_articles.items():
        lines.append(f"## {source}")
        if not articles:
            lines.append("最近 24 小時沒有新文章。")
            lines.append("")
            continue
        lines.append("| 日期 | 標題 |")
        lines.append("|------|------|")
        for a in articles:
            lines.append(f"| {a['date']} | [{a['title']}]({a['link']}) |")
        lines.append("")
        # 加上每篇文章的摘要
        for a in articles:
            if a.get("summary"):
                lines.append(f"**{a['title']}**")
                lines.append(f"{a['summary']}")
                lines.append("")
    return "\n".join(lines)


# --- LINE 通知 ---

def build_line_message(all_articles, today):
    """將摘要轉為 LINE 適合的純文字格式。"""
    lines = [f"📰 文章摘要 - {today}", ""]
    has_articles = False
    for source, articles in all_articles.items():
        if not articles:
            continue
        has_articles = True
        lines.append(f"【{source}】")
        for a in articles:
            lines.append(f"📌 {a['title']}")
            if a.get("summary"):
                lines.append(a["summary"])
            lines.append(f"🔗 {a['link']}")
            lines.append("")
        lines.append("---")
    if not has_articles:
        lines.append("今天沒有新文章。")
    return "\n".join(lines)


def send_line_message(text):
    """發送訊息到 LINE 群組。"""
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    group_id = os.getenv("LINE_GROUP_ID")
    if not token or not group_id:
        print("  未設定 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_GROUP_ID，跳過 LINE 通知")
        return False

    # LINE 訊息限制 5000 字元
    if len(text) > 5000:
        text = text[:4990] + "\n..."

    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "to": group_id,
            "messages": [{"type": "text", "text": text}],
        },
        timeout=15,
    )
    if resp.status_code == 200:
        print("  LINE 訊息發送成功")
        return True
    else:
        print(f"  LINE 發送失敗: {resp.status_code} {resp.text}")
        return False


# --- 前置檢查 ---

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


# --- 主程式 ---

def main():
    run_preflight_checks()

    today = datetime.now().strftime("%Y-%m-%d")
    all_articles = {}

    # RSS sources
    for source, url in RSS_FEEDS.items():
        print(f"抓取 {source} ...")
        try:
            articles = fetch_recent_articles(url)
        except Exception as e:
            print(f"  抓取失敗，跳過: {e}")
            articles = []
        all_articles[source] = articles
        print(f"  找到 {len(articles)} 篇最近 {DAYS} 天的文章")

    # Scrape sources
    print("抓取 Mind the Product ...")
    try:
        articles = scrape_mindtheproduct()
    except Exception as e:
        print(f"  抓取失敗，跳過: {e}")
        articles = []
    all_articles["Mind the Product"] = articles
    print(f"  找到 {len(articles)} 篇最近 {DAYS} 天的文章")

    # AI 摘要
    summarize_all_articles(all_articles)

    # Markdown 產出
    md = build_markdown(all_articles, today)
    print("\n" + md)

    os.makedirs("output", exist_ok=True)
    output_path = os.path.join("output", f"digest_{today}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"\n已寫入 {output_path}")

    # LINE 通知
    print("\n發送 LINE 通知 ...")
    line_msg = build_line_message(all_articles, today)
    send_line_message(line_msg)


if __name__ == "__main__":
    main()
