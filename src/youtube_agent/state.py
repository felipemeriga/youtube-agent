from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class TrendItem(TypedDict):
    title: str
    source: str
    url: str
    score: int
    summary: str


class VideoData(TypedDict):
    video_id: str
    title: str
    views: int
    likes: int
    comments: int
    published_at: str
    channel_id: str


class ChannelStats(TypedDict):
    channel_id: str
    total_views: int
    subscriber_count: int
    video_count: int
    top_videos: list[VideoData]


class CompetitorVideo(TypedDict):
    channel_name: str
    video_id: str
    title: str
    views: int
    likes: int
    published_at: str


class TopicSuggestion(TypedDict):
    title: str
    angle: str
    timeliness: str
    estimated_interest: str


class ResearchFinding(TypedDict):
    query: str
    source: str
    content: str
    tool: str


class VideoOutline(TypedDict):
    sections: list[dict[str, str]]
    hooks: list[str]
    estimated_duration: str


class VideoScript(TypedDict):
    content: str
    word_count: int


class VideoMetadata(TypedDict):
    title_options: list[str]
    description: str
    tags: list[str]
    thumbnail_texts: list[str]


class IdeationState(TypedDict):
    trends: Annotated[list[TrendItem], operator.add]
    channel_stats: ChannelStats | None
    competitor_insights: list[CompetitorVideo]
    suggested_topics: list[TopicSuggestion]
    selected_topic: TopicSuggestion | None
    prompt: str


class ProductionState(TypedDict):
    topic: TopicSuggestion
    prompt: str
    research_findings: Annotated[list[ResearchFinding], operator.add]
    outline: VideoOutline | None
    script: VideoScript | None
    metadata: VideoMetadata | None


class OrchestratorState(TypedDict):
    selected_topic: TopicSuggestion | None
    topic: TopicSuggestion | None
    mode: str
    prompt: str
