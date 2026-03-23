from __future__ import annotations

import logging

import httpx

from youtube_agent.state import TrendItem

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "youtube-agent/0.1.0"}


def fetch_subreddit_trending(subreddit_name: str, limit: int = 10) -> list[TrendItem]:
    items: list[TrendItem] = []
    try:
        url = f"https://www.reddit.com/r/{subreddit_name}/hot.json?limit={limit}"
        response = httpx.get(url, headers=_HEADERS, timeout=10, follow_redirects=True)
        response.raise_for_status()
        data = response.json()
        for post in data.get("data", {}).get("children", []):
            post_data = post.get("data", {})
            if post_data.get("stickied"):
                continue
            items.append(
                TrendItem(
                    title=post_data.get("title", ""),
                    source="reddit",
                    url=f"https://reddit.com{post_data.get('permalink', '')}",
                    score=post_data.get("score", 0),
                    summary=post_data.get("selftext", "")[:200],
                )
            )
    except Exception as e:
        logger.warning("Failed to fetch r/%s: %s", subreddit_name, e)
    return items


def fetch_multiple_subreddits(
    subreddit_names: list[str], limit_per_sub: int = 10
) -> list[TrendItem]:
    all_items: list[TrendItem] = []
    for name in subreddit_names:
        all_items.extend(fetch_subreddit_trending(name, limit=limit_per_sub))
    return all_items
