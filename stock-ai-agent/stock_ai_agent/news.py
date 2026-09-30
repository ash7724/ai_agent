from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

import feedparser
import requests

from config import NEWS_API_KEY


def google_news(ticker: str, company_name: str | None = None, limit: int = 15) -> list[dict]:
    query = company_name or ticker
    url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    )

    feed = feedparser.parse(url)
    items = []

    for entry in feed.entries[:limit]:
        published = entry.get("published", "")
        items.append({
            "title": entry.get("title", "").strip(),
            "source": entry.get("source", {}).get("title", "") if hasattr(entry.get("source", {}), "get") else "",
            "published": published,
            "url": entry.get("link", ""),
        })

    return items


def newsapi_search(query: str, limit: int = 15) -> list[dict]:
    if not NEWS_API_KEY:
        return []

    r = requests.get(
        "https://newsapi.org/v2/everything",
        params={
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": limit,
        },
        headers={"X-Api-Key": NEWS_API_KEY},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()

    return [
        {
            "title": a.get("title", ""),
            "source": (a.get("source") or {}).get("name", ""),
            "published": a.get("publishedAt", ""),
            "url": a.get("url", ""),
            "description": a.get("description", ""),
        }
        for a in data.get("articles", [])
    ]


def collect_news(ticker: str, company_name: str | None = None, use_newsapi: bool = False) -> list[dict]:
    items = google_news(ticker, company_name)

    if use_newsapi and NEWS_API_KEY:
        try:
            items += newsapi_search(company_name or ticker)
        except Exception:
            pass

    # Remove duplicate titles.
    seen = set()
    unique = []
    for item in items:
        key = item.get("title", "").lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(item)

    return unique[:25]
