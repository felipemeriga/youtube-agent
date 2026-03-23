from __future__ import annotations

import logging

import httpx

from youtube_agent.state import TrendItem

logger = logging.getLogger(__name__)

_BASE_URL = "https://hacker-news.firebaseio.com/v0"


async def fetch_top_stories(limit: int = 20) -> list[TrendItem]:
    items: list[TrendItem] = []
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{_BASE_URL}/topstories.json")
        response.raise_for_status()
        story_ids = response.json()[:limit]
        for story_id in story_ids:
            try:
                resp = await client.get(f"{_BASE_URL}/item/{story_id}.json")
                resp.raise_for_status()
                data = resp.json()
                if data and data.get("type") == "story":
                    items.append(
                        TrendItem(
                            title=data.get("title", ""),
                            source="hackernews",
                            url=data.get(
                                "url",
                                f"https://news.ycombinator.com/item?id={story_id}",
                            ),
                            score=data.get("score", 0),
                            summary="",
                        )
                    )
            except Exception as e:
                logger.warning("Failed to fetch HN story %s: %s", story_id, e)
    return items
