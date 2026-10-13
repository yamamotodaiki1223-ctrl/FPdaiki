"""
大手・信頼度の高いニュースサイトから経済・お金に関わる記事をピックアップし、
LINE公式アカウントのPush APIで(自分一人だけに)1日1回配信するスクリプト。

GitHub Actions の日次cronから実行される想定。
"""
import os
import time
from itertools import zip_longest
from urllib.parse import quote_plus

import feedparser
import requests

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

# --- 信頼できる情報源として限定する大手メディアのドメイン ---
TRUSTED_DOMAINS = [
    "nhk.or.jp",       # NHK
    "nikkei.com",      # 日本経済新聞
    "reuters.com",     # ロイター
    "jiji.com",        # 時事通信
    "asahi.com",       # 朝日新聞
    "yomiuri.co.jp",   # 読売新聞
    "mainichi.jp",     # 毎日新聞
    "kyodonews.jp",    # 共同通信
    "toyokeizai.net",  # 東洋経済オンライン
    "diamond.jp",      # ダイヤモンド・オンライン
]

# 経済全体の大きな動き(重要トピック側)。個別株・企業決算に寄りすぎないよう、
# 株価そのものより暮らし・政策に近いマクロ指標を中心に選定している。
MACRO_KEYWORDS = [
    "物価", "金利", "円安", "円高", "日銀", "税制", "社会保険",
    "年金", "最低賃金", "賃上げ", "インフレ",
]

# FPの活動(家計相談・情報発信)に直結する個人のお金の話題(教育費以外)
PERSONAL_FINANCE_KEYWORDS = [
    "家計", "NISA", "iDeCo", "保険", "住宅ローン", "児童手当", "扶養控除",
    "相続", "贈与税", "ふるさと納税", "医療費", "介護",
    "年収の壁", "確定申告", "消費税",
]

# 教育費関連(専用メッセージとして分けて配信する)
EDUCATION_COST_KEYWORDS = [
    "教育費", "学費", "授業料", "奨学金", "高校無償化", "大学無償化",
    "幼児教育無償化", "教育ローン", "学資保険", "入学金", "塾代",
]


def google_news_url(keywords, domains=TRUSTED_DOMAINS, when="1d"):
    keyword_part = " OR ".join(keywords)
    site_part = " OR ".join(f"site:{d}" for d in domains)
    query = f"{keyword_part} ({site_part}) when:{when}"
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=ja&gl=JP&ceid=JP:ja"


# --- ニュースソースをグループ単位で定義 ---
# いずれも「経済ニュースであること」または「信頼できる大手メディアの経済・お金関連記事であること」で
# 事前に絞り込み済みのため、記事単位でのキーワード再フィルタは行わない。
GROUPS = [
    {
        "heading": "【本日の経済ニュース】",
        "sources": [
            {"name": "Yahoo!ニュース(経済)", "url": "https://news.yahoo.co.jp/rss/topics/business.xml"},
            {"name": "経済・政策ニュース", "url": google_news_url(MACRO_KEYWORDS)},
            {"name": "家計・お金ニュース", "url": google_news_url(PERSONAL_FINANCE_KEYWORDS)},
        ],
        "max_articles": 15,
    },
    {
        "heading": "【本日の教育費関連ニュース】",
        "sources": [
            {"name": "教育費ニュース", "url": google_news_url(EDUCATION_COST_KEYWORDS)},
        ],
        "max_articles": 10,
    },
]

LOOKBACK_HOURS = 30  # 前回実行からの取りこぼしを防ぐため24時間より広めに取る
PER_SOURCE_CAP = 6  # 1ソースが枠を独占しないための上限


def fetch_group_articles(group, seen_links, seen_titles):
    cutoff = time.time() - LOOKBACK_HOURS * 3600
    by_source = []

    for source in group["sources"]:
        feed = feedparser.parse(source["url"])
        source_articles = []

        for entry in feed.entries:
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published is not None:
                entry_time = time.mktime(published)
                if entry_time < cutoff:
                    continue

            title = entry.get("title", "")
            link = entry.get("link", "")
            title_key = title[:30]
            if link in seen_links or title_key in seen_titles:
                continue
            seen_links.add(link)
            seen_titles.add(title_key)

            source_articles.append({
                "source": source["name"],
                "title": title,
                "link": link,
            })
            if len(source_articles) >= PER_SOURCE_CAP:
                break

        by_source.append(source_articles)

    # ソースごとに交互に取り出す(ラウンドロビン)ことで、特定ソースの偏りを防ぐ
    interleaved = []
    for row in zip_longest(*by_source):
        for article in row:
            if article is not None:
                interleaved.append(article)

    return interleaved[:group["max_articles"]]


def build_message(heading, articles):
    if not articles:
        return None

    lines = [heading]
    for article in articles:
        lines.append(f"\n■{article['title']}（{article['source']}）\n{article['link']}")

    return "\n".join(lines)


def send_to_line(messages):
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": text} for text in messages],
    }

    response = requests.post(LINE_PUSH_URL, headers=headers, json=payload, timeout=15)
    response.raise_for_status()


def main():
    seen_links = set()
    seen_titles = set()
    messages = []

    for group in GROUPS:
        articles = fetch_group_articles(group, seen_links, seen_titles)
        message = build_message(group["heading"], articles)
        if message is not None:
            messages.append(message)
            print(f"{group['heading']}: {len(articles)}件")
        else:
            print(f"{group['heading']}: 該当記事なし")

    if not messages:
        print("配信する記事がないため、配信をスキップします。")
        return

    send_to_line(messages)
    print("LINEに配信しました。")


if __name__ == "__main__":
    main()
