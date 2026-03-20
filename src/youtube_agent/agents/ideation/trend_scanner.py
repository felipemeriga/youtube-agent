from __future__ import annotations

import asyncio
import logging

from youtube_agent.config import AppConfig
from youtube_agent.state import IdeationState
from youtube_agent.tools.hackernews import fetch_top_stories
from youtube_agent.tools.news_feeds import fetch_feeds
from youtube_agent.tools.reddit import fetch_multiple_subreddits
from youtube_agent.tools.youtube_api import YouTubeClient

logger = logging.getLogger(__name__)


async def _scan_trends_async(state: IdeationState, config: AppConfig) -> dict:
    all_trends = []

    try:
        hn_trends = await fetch_top_stories(limit=15)
        all_trends.extend(hn_trends)
    except Exception as e:
        logger.warning("HackerNews scan failed: %s", e)

    try:
        reddit_trends = fetch_multiple_subreddits(config.reddit.subreddits, limit_per_sub=10)
        all_trends.extend(reddit_trends)
    except Exception as e:
        logger.warning("Reddit scan failed: %s", e)

    try:
        rss_trends = fetch_feeds(config.news.feeds, limit_per_feed=10)
        all_trends.extend(rss_trends)
    except Exception as e:
        logger.warning("RSS feed scan failed: %s", e)

    try:
        yt_client = YouTubeClient()
        yt_trends = yt_client.search_trending("software development career", max_results=10)
        all_trends.extend(yt_trends)
    except Exception as e:
        logger.warning("YouTube trend scan failed: %s", e)

    return {"trends": all_trends}


def scan_trends(state: IdeationState, config: AppConfig) -> dict:
    return asyncio.run(_scan_trends_async(state, config))
