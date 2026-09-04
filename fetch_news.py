"""
教育・出産・子育て関連ニュースからお金に関わる記事をピックアップし、
LINE公式アカウントのBroadcast APIで1日1回配信するスクリプト。

GitHub Actions の日次cronから実行される想定。
"""
import os
import time
import feedparser
import requests

LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"

# --- ニュースソース定義 ---
# kind="edu":    教育・子育て専門サイト。お金キーワードでフィルタする。
# kind="money":  お金専門サイト。子育て・教育キーワードでフィルタする。
# kind="general":一般ニュース(Yahoo!ニュースなど)。お金キーワードでフィルタする。
# kind="google": Googleニュースの複合キーワード検索。検索クエリ自体で絞り込み済みのためフィルタ不要。
SOURCES = [
    {"name": "リセマム", "url": "https://resemom.jp/rss20/index.rdf", "kind": "edu"},
    {"name": "こどもまなび☆ラボ", "url": "https://kodomo-manabi-labo.net/feed", "kind": "edu"},
    {"name": "ファイナンシャルフィールド", "url": "https://financial-field.com/feed", "kind": "money"},
    {"name": "マネーの達人", "url": "https://manetatsu.com/rss20/index.rdf", "kind": "money"},
    {"name": "Yahoo!ニュース(経済)", "url": "https://news.yahoo.co.jp/rss/topics/business.xml", "kind": "money"},
    {"name": "Yahoo!ニュース(国内)", "url": "https://news.yahoo.co.jp/rss/topics/domestic.xml", "kind": "edu"},
    {
        "name": "Google News",
        "url": (
            "https://news.google.com/rss/search?q="
            "%E5%85%90%E7%AB%A5%E6%89%8B%E5%BD%93+OR+%E5%AD%A6%E8%B3%87%E4%BF%9D%E9%99%BA+OR+"
            "%E4%BF%9D%E8%82%B2%E6%96%99+OR+%E9%AB%98%E6%A0%A1%E7%84%A1%E5%84%9F%E5%8C%96+OR+"
            "%E8%82%B2%E5%85%90%E4%BC%91%E6%A5%AD%E7%B5%A6%E4%BB%98+OR+%E5%87%BA%E7%94%A3%E4%B8%80%E6%99%82%E9%87%91+OR+"
            "%E5%AD%90%E8%82%B2%E3%81%A6%E6%94%AF%E6%8F%B4%E9%87%91+OR+%E5%85%90%E7%AB%A5%E6%89%B6%E9%A4%8A%E6%89%8B%E5%BD%93+"
            "when:1d&hl=ja&gl=JP&ceid=JP:ja"
        ),
        "kind": "google",
    },
    {
        "name": "Google News",
        "url": (
            "https://news.google.com/rss/search?q="
            "(%E6%95%99%E8%82%B2%E8%B2%BB+OR+%E5%A5%A8%E5%AD%A6%E9%87%91+OR+%E6%89%B6%E9%A4%8A%E6%8E%A7%E9%99%A4+OR+NISA)+"
            "(%E5%AD%90%E8%82%B2%E3%81%A6+OR+%E5%AD%90%E3%81%A9%E3%82%82)+when:1d&hl=ja&gl=JP&ceid=JP:ja"
        ),
        "kind": "google",
    },
]

MONEY_KEYWORDS = [
    "児童手当", "教育費", "学資保険", "奨学金", "NISA", "ideco", "iDeCo",
    "扶養控除", "保育料", "高校無償化", "授業料", "出産手当金", "出産育児一時金",
    "育児休業給付", "育休給付", "医療費控除", "学費", "貯蓄", "家計", "年収",
    "保険料", "税制", "税金", "住民税", "所得控除", "給付金", "補助金", "助成金",
]

CHILD_EDU_KEYWORDS = [
    "子育て", "子ども", "こども", "教育費", "児童手当", "保育", "学資", "出産",
    "育児", "進学", "受験", "奨学金", "学校", "幼稚園", "保育園", "習い事",
    "子供", "小学校", "中学校", "高校", "大学",
]

LOOKBACK_HOURS = 30  # 前回実行からの取りこぼしを防ぐため24時間より広めに取る
MAX_ARTICLES = 12


def contains_keyword(text, keywords):
    return any(kw.lower() in text.lower() for kw in keywords)


KEYWORDS_BY_KIND = {
    "edu": MONEY_KEYWORDS,
    "general": MONEY_KEYWORDS,
    "money": CHILD_EDU_KEYWORDS,
}


def fetch_matching_entries():
    cutoff = time.time() - LOOKBACK_HOURS * 3600
    matched = []
    seen_links = set()
    seen_titles = set()

    for source in SOURCES:
        feed = feedparser.parse(source["url"])
        keywords = KEYWORDS_BY_KIND.get(source["kind"])  # kind="google" -> None(フィルタ不要)

        for entry in feed.entries:
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published is not None:
                entry_time = time.mktime(published)
                if entry_time < cutoff:
                    continue

            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if keywords is not None and not contains_keyword(title + " " + summary, keywords):
                continue

            link = entry.get("link", "")
            title_key = title[:30]
            if link in seen_links or title_key in seen_titles:
                continue
            seen_links.add(link)
            seen_titles.add(title_key)

            matched.append({
                "source": source["name"],
                "title": title,
                "link": link,
            })

    return matched


def build_message(articles):
    if not articles:
        return None

    lines = ["【本日の教育・子育てお金ニュース】"]
    for article in articles[:MAX_ARTICLES]:
        lines.append(f"\n■{article['title']}（{article['source']}）\n{article['link']}")

    return "\n".join(lines)


def send_to_line(message):
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"messages": [{"type": "text", "text": message}]}

    response = requests.post(LINE_BROADCAST_URL, headers=headers, json=payload, timeout=15)
    response.raise_for_status()


def main():
    articles = fetch_matching_entries()
    message = build_message(articles)

    if message is None:
        print("該当記事なし。配信をスキップします。")
        return

    send_to_line(message)
    print(f"{len(articles[:MAX_ARTICLES])}件の記事をLINEに配信しました。")


if __name__ == "__main__":
    main()
