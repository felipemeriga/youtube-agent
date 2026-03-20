from __future__ import annotations

import logging

from youtube_agent.config import AppConfig
from youtube_agent.state import AnalyticsState
from youtube_agent.tools.youtube_api import YouTubeClient

logger = logging.getLogger(__name__)


def fetch_data(state: AnalyticsState, config: AppConfig) -> dict:
    result: dict = {"channel_videos": [], "competitor_videos": []}

    if not config.youtube.channel_id:
        logger.warning("No YouTube channel_id configured")
        return result

    try:
        yt_client = YouTubeClient()
        videos = yt_client.get_channel_videos(
            config.youtube.channel_id, max_results=config.youtube.max_videos
        )
        result["channel_videos"] = videos
    except Exception as e:
        logger.warning("Failed to fetch channel videos: %s", e)

    if config.youtube.competitor_channel_ids:
        try:
            yt_client = YouTubeClient()
            for cid in config.youtube.competitor_channel_ids:
                try:
                    comp_videos = yt_client.get_channel_videos(cid, max_results=10)
                    result["competitor_videos"].extend(comp_videos)
                except Exception as e:
                    logger.warning("Failed to fetch competitor %s: %s", cid, e)
        except Exception as e:
            logger.warning("Competitor fetch failed: %s", e)

    return result
