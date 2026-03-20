from __future__ import annotations

import logging

from youtube_agent.config import AppConfig
from youtube_agent.state import IdeationState
from youtube_agent.tools.youtube_api import YouTubeClient

logger = logging.getLogger(__name__)


def analyze_channel(state: IdeationState, config: AppConfig) -> dict:
    result: dict = {"channel_stats": None, "competitor_insights": []}

    if not config.youtube.channel_id:
        logger.warning("No YouTube channel_id configured, skipping channel analysis")
        return result

    try:
        yt_client = YouTubeClient()
        stats = yt_client.get_channel_stats(config.youtube.channel_id)
        result["channel_stats"] = stats
    except Exception as e:
        logger.warning("Channel stats fetch failed: %s", e)

    if config.youtube.competitor_channel_ids:
        try:
            yt_client = YouTubeClient()
            competitors = yt_client.get_competitor_videos(
                config.youtube.competitor_channel_ids, max_per_channel=10
            )
            result["competitor_insights"] = competitors
        except Exception as e:
            logger.warning("Competitor analysis failed: %s", e)

    return result
