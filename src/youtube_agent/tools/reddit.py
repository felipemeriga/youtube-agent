from __future__ import annotations

import logging
import os

import praw

from youtube_agent.state import TrendItem

logger = logging.getLogger(__name__)


def _create_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=os.environ.get("REDDIT_CLIENT_ID", ""),
        client_secret=os.environ.get("REDDIT_CLIENT_SECRET", ""),
        user_agent=os.environ.get("REDDIT_USER_AGENT", "youtube-agent/0.1.0"),
    )


def fetch_subreddit_trending(subreddit_name: str, limit: int = 10) -> list[TrendItem]:
    items: list[TrendItem] = []
    try:
        reddit = _create_reddit_client()
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.hot(limit=limit):
            items.append(
                TrendItem(
                    title=submission.title,
                    source="reddit",
                    url=submission.url,
                    score=submission.score,
                    summary=submission.selftext[:200] if submission.selftext else "",
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
