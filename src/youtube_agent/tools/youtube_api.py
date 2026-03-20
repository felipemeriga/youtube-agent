from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from googleapiclient.discovery import build

from youtube_agent.state import ChannelStats, CompetitorVideo, TrendItem, VideoData

logger = logging.getLogger(__name__)


class YouTubeClient:
    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("YOUTUBE_API_KEY", "")
        self._service = build("youtube", "v3", developerKey=self._api_key)

    def get_channel_videos(self, channel_id: str, max_results: int = 20) -> list[VideoData]:
        search_response = (
            self._service.search()
            .list(
                channelId=channel_id,
                part="id,snippet",
                order="date",
                maxResults=max_results,
                type="video",
            )
            .execute()
        )
        video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
        if not video_ids:
            return []
        stats_response = (
            self._service.videos().list(id=",".join(video_ids), part="snippet,statistics").execute()
        )
        videos: list[VideoData] = []
        for item in stats_response.get("items", []):
            stats = item.get("statistics", {})
            videos.append(
                VideoData(
                    video_id=item["id"],
                    title=item["snippet"]["title"],
                    views=int(stats.get("viewCount", 0)),
                    likes=int(stats.get("likeCount", 0)),
                    comments=int(stats.get("commentCount", 0)),
                    published_at=item["snippet"]["publishedAt"],
                    channel_id=channel_id,
                )
            )
        return videos

    def get_channel_stats(self, channel_id: str) -> ChannelStats:
        response = self._service.channels().list(id=channel_id, part="statistics").execute()
        item = response["items"][0]
        stats = item["statistics"]
        top_videos = sorted(
            self.get_channel_videos(channel_id, max_results=10),
            key=lambda v: v["views"],
            reverse=True,
        )[:5]
        return ChannelStats(
            channel_id=channel_id,
            total_views=int(stats.get("viewCount", 0)),
            subscriber_count=int(stats.get("subscriberCount", 0)),
            video_count=int(stats.get("videoCount", 0)),
            top_videos=top_videos,
        )

    def search_trending(self, query: str, max_results: int = 10) -> list[TrendItem]:
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")
        response = (
            self._service.search()
            .list(
                q=query,
                part="snippet",
                order="viewCount",
                maxResults=max_results,
                type="video",
                publishedAfter=thirty_days_ago,
            )
            .execute()
        )
        items: list[TrendItem] = []
        for item in response.get("items", []):
            items.append(
                TrendItem(
                    title=item["snippet"]["title"],
                    source="youtube",
                    url=f"https://youtube.com/watch?v={item['id']['videoId']}",
                    score=0,
                    summary=item["snippet"].get("description", "")[:200],
                )
            )
        return items

    def get_competitor_videos(
        self, channel_ids: list[str], max_per_channel: int = 10
    ) -> list[CompetitorVideo]:
        results: list[CompetitorVideo] = []
        for cid in channel_ids:
            try:
                videos = self.get_channel_videos(cid, max_results=max_per_channel)
                ch_response = self._service.channels().list(id=cid, part="snippet").execute()
                channel_name = (
                    ch_response["items"][0]["snippet"]["title"] if ch_response["items"] else cid
                )
                for v in videos:
                    results.append(
                        CompetitorVideo(
                            channel_name=channel_name,
                            video_id=v["video_id"],
                            title=v["title"],
                            views=v["views"],
                            likes=v["likes"],
                            published_at=v["published_at"],
                        )
                    )
            except Exception as e:
                logger.warning("Failed to fetch competitor channel %s: %s", cid, e)
        return results
