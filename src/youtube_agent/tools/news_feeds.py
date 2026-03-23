from __future__ import annotations

import logging

import feedparser

from youtube_agent.state import TrendItem

logger = logging.getLogger(__name__)


def fetch_feeds(feed_urls: list[str], limit_per_feed: int = 10) -> list[TrendItem]:
    items: list[TrendItem] = []
    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.get("entries", [])[:limit_per_feed]:
                items.append(
                    TrendItem(
                        title=entry.get("title", ""),
                        source="rss",
                        url=entry.get("link", ""),
                        score=0,
                        summary=entry.get("summary", "")[:200],
                    )
                )
        except Exception as e:
            logger.warning("Failed to parse feed %s: %s", url, e)
    return items
