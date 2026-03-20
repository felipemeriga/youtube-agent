# YouTube Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a LangGraph CLI tool that helps manage the "Além do Código" YouTube channel through content ideation, video production, and analytics pipelines.

**Architecture:** Three independent LangGraph sub-graphs (ideation, production, analytics) composed into a parent orchestrator. Each sub-graph can run independently via CLI. Human-in-the-loop checkpoints at key decision points. SQLite persistence by default.

**Tech Stack:** Python 3.10+, LangGraph, LangChain, Click, Rich, YouTube Data API v3, PRAW, httpx, feedparser, Tavily, Playwright, SQLite/PostgreSQL

**Spec:** `docs/superpowers/specs/2026-03-20-youtube-agent-design.md`

---

## File Structure

```
youtube-agent/
├── src/youtube_agent/
│   ├── __init__.py
│   ├── state.py              # All Pydantic models and TypedDict states
│   ├── graph.py              # Parent orchestrator
│   ├── cli.py                # Click CLI with Rich UI
│   ├── config.py             # Dataclass config from YAML + .env
│   ├── llm.py                # Multi-provider LLM factory
│   ├── display.py            # Rich console helpers
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── ideation/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py
│   │   │   ├── trend_scanner.py
│   │   │   ├── channel_analyzer.py
│   │   │   └── topic_generator.py
│   │   ├── production/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py
│   │   │   ├── researcher.py
│   │   │   ├── outliner.py
│   │   │   ├── writer.py
│   │   │   └── metadata_generator.py
│   │   └── analytics/
│   │       ├── __init__.py
│   │       ├── graph.py
│   │       ├── data_fetcher.py
│   │       ├── analyzer.py
│   │       └── strategist.py
│   └── tools/
│       ├── __init__.py
│       ├── youtube_api.py
│       ├── hackernews.py
│       ├── reddit.py
│       ├── news_feeds.py
│       ├── tavily_search.py
│       └── scraper.py
├── tests/
│   ├── __init__.py
│   ├── test_tools/
│   │   ├── __init__.py
│   │   ├── test_youtube_api.py
│   │   ├── test_hackernews.py
│   │   ├── test_reddit.py
│   │   ├── test_news_feeds.py
│   │   └── test_tavily_search.py
│   ├── test_ideation/
│   │   ├── __init__.py
│   │   └── test_ideation_graph.py
│   ├── test_production/
│   │   ├── __init__.py
│   │   └── test_production_graph.py
│   ├── test_analytics/
│   │   ├── __init__.py
│   │   └── test_analytics_graph.py
│   ├── test_config.py
│   ├── test_llm.py
│   └── test_state.py
├── pyproject.toml
├── config.yaml
├── .env.example
├── .gitignore
└── output/                   # gitignored
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `config.yaml`
- Create: `src/youtube_agent/__init__.py`

- [ ] **Step 1: Initialize git repo**

```bash
cd /Users/feliperamosdasilva/personal_projects/youtube-agent
git init
git checkout -b main
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[project]
name = "youtube-agent"
version = "0.1.0"
description = "YouTube channel agent for Além do Código — powered by LangGraph"
requires-python = ">=3.10"
dependencies = [
    "langchain>=0.3.28,<0.4",
    "langchain-core>=0.3,<0.4",
    "langgraph>=0.6.11,<0.7",
    "langchain-anthropic>=0.3.22",
    "langchain-openai>=0.3.35",
    "langchain-google-genai>=2.1",
    "langchain-tavily>=0.2.11",
    "langgraph-checkpoint-sqlite>=2.0",
    "langgraph-checkpoint-postgres>=2.0.25",
    "playwright>=1.49",
    "google-api-python-client>=2.0",
    "praw>=7.0",
    "httpx>=0.27",
    "feedparser>=6.0",
    "pydantic>=2.0",
    "click>=8.1",
    "rich>=13.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.8",
]

[project.scripts]
youtube-agent = "youtube_agent.cli:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/youtube_agent"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
asyncio_mode = "auto"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg
.env
.venv/
venv/
output/
*.db
.ruff_cache/
.pytest_cache/
```

- [ ] **Step 4: Create .env.example**

```
# LLM Provider (at least one required)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# YouTube Data API v3
YOUTUBE_API_KEY=

# Tavily Search
TAVILY_API_KEY=

# Reddit API
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=youtube-agent/0.1.0

# PostgreSQL (optional — SQLite used by default)
DATABASE_URL=
```

- [ ] **Step 5: Create config.yaml**

```yaml
llm:
  provider: "openai"
  model: "gpt-4o-mini"
  temperature: 0.3

youtube:
  channel_id: ""
  competitor_channel_ids: []
  max_videos: 20

reddit:
  subreddits:
    - "brdev"
    - "cscareerquestions"
    - "ExperiencedDevs"

news:
  feeds:
    - "https://dev.to/feed"
    - "https://www.infoq.com/feed/"
    - "https://techcrunch.com/feed/"

output:
  dir: "./output"

persistence:
  backend: "sqlite"
  sqlite_path: "./youtube_agent.db"
```

- [ ] **Step 6: Create src/youtube_agent/__init__.py**

```python
"""YouTube channel agent for Além do Código."""
```

- [ ] **Step 7: Create output directory and all __init__.py files**

```bash
mkdir -p output
mkdir -p src/youtube_agent/agents/ideation
mkdir -p src/youtube_agent/agents/production
mkdir -p src/youtube_agent/agents/analytics
mkdir -p src/youtube_agent/tools
mkdir -p tests/test_tools tests/test_ideation tests/test_production tests/test_analytics
touch src/youtube_agent/agents/__init__.py
touch src/youtube_agent/agents/ideation/__init__.py
touch src/youtube_agent/agents/production/__init__.py
touch src/youtube_agent/agents/analytics/__init__.py
touch src/youtube_agent/tools/__init__.py
touch tests/__init__.py
touch tests/test_tools/__init__.py
touch tests/test_ideation/__init__.py
touch tests/test_production/__init__.py
touch tests/test_analytics/__init__.py
```

- [ ] **Step 8: Install dependencies**

```bash
uv sync
```

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml .gitignore .env.example config.yaml src/ tests/ output/.gitkeep
git commit -m "chore: scaffold youtube-agent project"
```

---

### Task 2: Config Module

**Files:**
- Create: `src/youtube_agent/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing test for config loading**

```python
# tests/test_config.py
from youtube_agent.config import AppConfig, load_config


def test_load_config_defaults():
    config = load_config(config_path="/nonexistent/path.yaml")
    assert config.llm.provider == "openai"
    assert config.llm.model == "gpt-4o-mini"
    assert config.llm.temperature == 0.3
    assert config.youtube.max_videos == 20
    assert config.persistence.backend == "sqlite"


def test_load_config_from_yaml(tmp_path):
    yaml_content = """
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  temperature: 0.5
youtube:
  channel_id: "UC123"
  competitor_channel_ids: ["UC456"]
  max_videos: 10
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)
    config = load_config(config_path=str(config_file))
    assert config.llm.provider == "anthropic"
    assert config.youtube.channel_id == "UC123"
    assert config.youtube.max_videos == 10
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_config.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement config.py**

```python
# src/youtube_agent/config.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

_DEFAULT_CONFIG_PATH = "config.yaml"


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.3


@dataclass
class YouTubeConfig:
    channel_id: str = ""
    competitor_channel_ids: list[str] = field(default_factory=list)
    max_videos: int = 20


@dataclass
class RedditConfig:
    subreddits: list[str] = field(
        default_factory=lambda: ["brdev", "cscareerquestions", "ExperiencedDevs"]
    )


@dataclass
class NewsConfig:
    feeds: list[str] = field(
        default_factory=lambda: [
            "https://dev.to/feed",
            "https://www.infoq.com/feed/",
            "https://techcrunch.com/feed/",
        ]
    )


@dataclass
class OutputConfig:
    dir: str = "./output"


@dataclass
class PersistenceConfig:
    backend: str = "sqlite"
    sqlite_path: str = "./youtube_agent.db"
    postgres_url: str = ""


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    youtube: YouTubeConfig = field(default_factory=YouTubeConfig)
    reddit: RedditConfig = field(default_factory=RedditConfig)
    news: NewsConfig = field(default_factory=NewsConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    persistence: PersistenceConfig = field(default_factory=PersistenceConfig)


def load_config(config_path: str | None = None) -> AppConfig:
    load_dotenv()
    path = Path(config_path or _DEFAULT_CONFIG_PATH)
    if not path.exists():
        return AppConfig()
    raw = yaml.safe_load(path.read_text()) or {}
    return AppConfig(
        llm=LLMConfig(**raw.get("llm", {})),
        youtube=YouTubeConfig(**raw.get("youtube", {})),
        reddit=RedditConfig(**raw.get("reddit", {})),
        news=NewsConfig(**raw.get("news", {})),
        output=OutputConfig(**raw.get("output", {})),
        persistence=PersistenceConfig(**raw.get("persistence", {})),
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_config.py -v
```

Expected: PASS

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/config.py tests/test_config.py
uv run ruff format src/youtube_agent/config.py tests/test_config.py
git add src/youtube_agent/config.py tests/test_config.py
git commit -m "feat: add config module with YAML loading"
```

---

### Task 3: LLM Factory

**Files:**
- Create: `src/youtube_agent/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_llm.py
import pytest

from youtube_agent.config import LLMConfig
from youtube_agent.llm import create_llm


def test_create_llm_unsupported_provider():
    config = LLMConfig(provider="unsupported")
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_llm(config)


def test_create_llm_openai():
    config = LLMConfig(provider="openai", model="gpt-4o-mini", temperature=0.3)
    llm = create_llm(config)
    assert llm is not None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_llm.py -v
```

- [ ] **Step 3: Implement llm.py**

```python
# src/youtube_agent/llm.py
from __future__ import annotations

import importlib

from langchain_core.language_models import BaseChatModel

from youtube_agent.config import LLMConfig

_PROVIDERS: dict[str, tuple[str, str]] = {
    "anthropic": ("langchain_anthropic", "ChatAnthropic"),
    "openai": ("langchain_openai", "ChatOpenAI"),
    "google": ("langchain_google_genai", "ChatGoogleGenerativeAI"),
}


def create_llm(config: LLMConfig) -> BaseChatModel:
    if config.provider not in _PROVIDERS:
        raise ValueError(
            f"Unsupported LLM provider: {config.provider}. "
            f"Supported: {', '.join(_PROVIDERS)}"
        )
    module_name, class_name = _PROVIDERS[config.provider]
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls(model=config.model, temperature=config.temperature)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_llm.py -v
```

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/llm.py tests/test_llm.py
uv run ruff format src/youtube_agent/llm.py tests/test_llm.py
git add src/youtube_agent/llm.py tests/test_llm.py
git commit -m "feat: add multi-provider LLM factory"
```

---

### Task 4: State Types

**Files:**
- Create: `src/youtube_agent/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_state.py
from youtube_agent.state import (
    AnalyticsState,
    IdeationState,
    OrchestratorState,
    ProductionState,
    TopicSuggestion,
    TrendItem,
    VideoData,
)


def test_trend_item_creation():
    item = TrendItem(
        title="Python 4.0 Released",
        source="hackernews",
        url="https://example.com",
        score=500,
        summary="New Python version released",
    )
    assert item["title"] == "Python 4.0 Released"
    assert item["source"] == "hackernews"


def test_topic_suggestion_creation():
    topic = TopicSuggestion(
        title="Como conseguir emprego na Europa",
        angle="Guia prático para devs brasileiros",
        timeliness="Alta demanda por devs em Portugal",
        estimated_interest="high",
    )
    assert topic["title"] == "Como conseguir emprego na Europa"


def test_ideation_state_has_required_keys():
    state: IdeationState = {
        "trends": [],
        "channel_stats": None,
        "competitor_insights": [],
        "suggested_topics": [],
        "selected_topic": None,
    }
    assert "trends" in state


def test_video_data_creation():
    video = VideoData(
        video_id="abc123",
        title="Test Video",
        views=1000,
        likes=50,
        comments=10,
        published_at="2026-01-01",
        channel_id="UC123",
    )
    assert video["views"] == 1000
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_state.py -v
```

- [ ] **Step 3: Implement state.py**

```python
# src/youtube_agent/state.py
from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class TrendItem(TypedDict):
    title: str
    source: str  # "hackernews", "reddit", "rss", "youtube"
    url: str
    score: int
    summary: str


class ChannelStats(TypedDict):
    channel_id: str
    total_views: int
    subscriber_count: int
    video_count: int
    top_videos: list[VideoData]


class VideoData(TypedDict):
    video_id: str
    title: str
    views: int
    likes: int
    comments: int
    published_at: str
    channel_id: str


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
    estimated_interest: str  # "high", "medium", "low"


class ResearchFinding(TypedDict):
    query: str
    source: str
    content: str
    tool: str


class VideoOutline(TypedDict):
    sections: list[dict[str, str]]  # {"title": ..., "description": ..., "duration": ...}
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


class AnalysisReport(TypedDict):
    top_performing: list[VideoData]
    bottom_performing: list[VideoData]
    patterns: str
    competitor_comparison: str


class StrategyReport(TypedDict):
    content_suggestions: str
    title_patterns: str
    posting_recommendations: str
    growth_opportunities: str


# --- Sub-graph states ---


class IdeationState(TypedDict):
    trends: Annotated[list[TrendItem], operator.add]
    channel_stats: ChannelStats | None
    competitor_insights: list[CompetitorVideo]
    suggested_topics: list[TopicSuggestion]
    selected_topic: TopicSuggestion | None


class ProductionState(TypedDict):
    topic: TopicSuggestion
    research_findings: Annotated[list[ResearchFinding], operator.add]
    outline: VideoOutline | None
    script: VideoScript | None
    metadata: VideoMetadata | None


class AnalyticsState(TypedDict):
    channel_videos: list[VideoData]
    competitor_videos: list[VideoData]
    analysis: AnalysisReport | None
    strategy: StrategyReport | None


class OrchestratorState(TypedDict):
    selected_topic: TopicSuggestion | None
    topic: TopicSuggestion | None  # mapped from selected_topic for production
    mode: str  # "ideate", "produce", "analyze", "full"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_state.py -v
```

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/state.py tests/test_state.py
uv run ruff format src/youtube_agent/state.py tests/test_state.py
git add src/youtube_agent/state.py tests/test_state.py
git commit -m "feat: add all state types and Pydantic models"
```

---

### Task 5: YouTube API Tool

**Files:**
- Create: `src/youtube_agent/tools/youtube_api.py`
- Create: `tests/test_tools/test_youtube_api.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_tools/test_youtube_api.py
from unittest.mock import MagicMock, patch

from youtube_agent.tools.youtube_api import YouTubeClient


def test_youtube_client_init():
    with patch("youtube_agent.tools.youtube_api.build") as mock_build:
        mock_build.return_value = MagicMock()
        client = YouTubeClient(api_key="test-key")
        assert client is not None
        mock_build.assert_called_once_with("youtube", "v3", developerKey="test-key")


def test_get_channel_videos():
    with patch("youtube_agent.tools.youtube_api.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_search = MagicMock()
        mock_service.search.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": {"videoId": "vid1"},
                    "snippet": {"title": "Test Video", "publishedAt": "2026-01-01T00:00:00Z"},
                }
            ]
        }
        mock_service.videos.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "vid1",
                    "snippet": {"title": "Test Video", "publishedAt": "2026-01-01T00:00:00Z"},
                    "statistics": {"viewCount": "1000", "likeCount": "50", "commentCount": "10"},
                }
            ]
        }

        client = YouTubeClient(api_key="test-key")
        videos = client.get_channel_videos("UC123", max_results=5)
        assert len(videos) == 1
        assert videos[0]["title"] == "Test Video"
        assert videos[0]["views"] == 1000
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_tools/test_youtube_api.py -v
```

- [ ] **Step 3: Implement youtube_api.py**

```python
# src/youtube_agent/tools/youtube_api.py
from __future__ import annotations

import logging
import os

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
            .list(channelId=channel_id, part="id,snippet", order="date", maxResults=max_results, type="video")
            .execute()
        )
        video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]
        if not video_ids:
            return []
        stats_response = (
            self._service.videos()
            .list(id=",".join(video_ids), part="snippet,statistics")
            .execute()
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
        response = (
            self._service.channels()
            .list(id=channel_id, part="statistics")
            .execute()
        )
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
        from datetime import datetime, timedelta
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")
        response = (
            self._service.search()
            .list(q=query, part="snippet", order="viewCount", maxResults=max_results, type="video", publishedAfter=thirty_days_ago)
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
                # Get channel name
                ch_response = (
                    self._service.channels().list(id=cid, part="snippet").execute()
                )
                channel_name = ch_response["items"][0]["snippet"]["title"] if ch_response["items"] else cid
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_tools/test_youtube_api.py -v
```

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/tools/youtube_api.py tests/test_tools/test_youtube_api.py
uv run ruff format src/youtube_agent/tools/youtube_api.py tests/test_tools/test_youtube_api.py
git add src/youtube_agent/tools/youtube_api.py tests/test_tools/test_youtube_api.py
git commit -m "feat: add YouTube Data API v3 client"
```

---

### Task 6: HackerNews Tool

**Files:**
- Create: `src/youtube_agent/tools/hackernews.py`
- Create: `tests/test_tools/test_hackernews.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_tools/test_hackernews.py
from unittest.mock import AsyncMock, patch

import pytest

from youtube_agent.tools.hackernews import fetch_top_stories


@pytest.mark.asyncio
async def test_fetch_top_stories():
    mock_response_ids = AsyncMock()
    mock_response_ids.json.return_value = [1, 2]
    mock_response_ids.raise_for_status = lambda: None

    mock_response_item1 = AsyncMock()
    mock_response_item1.json.return_value = {
        "id": 1,
        "title": "Show HN: My Project",
        "url": "https://example.com",
        "score": 200,
        "type": "story",
    }
    mock_response_item1.raise_for_status = lambda: None

    mock_response_item2 = AsyncMock()
    mock_response_item2.json.return_value = {
        "id": 2,
        "title": "Ask HN: Best language?",
        "url": "",
        "score": 150,
        "type": "story",
    }
    mock_response_item2.raise_for_status = lambda: None

    with patch("youtube_agent.tools.hackernews.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = [mock_response_ids, mock_response_item1, mock_response_item2]

        results = await fetch_top_stories(limit=2)
        assert len(results) == 2
        assert results[0]["source"] == "hackernews"
        assert results[0]["title"] == "Show HN: My Project"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_tools/test_hackernews.py -v
```

- [ ] **Step 3: Implement hackernews.py**

```python
# src/youtube_agent/tools/hackernews.py
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
                            url=data.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                            score=data.get("score", 0),
                            summary="",
                        )
                    )
            except Exception as e:
                logger.warning("Failed to fetch HN story %s: %s", story_id, e)
    return items
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_tools/test_hackernews.py -v
```

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/tools/hackernews.py tests/test_tools/test_hackernews.py
uv run ruff format src/youtube_agent/tools/hackernews.py tests/test_tools/test_hackernews.py
git add src/youtube_agent/tools/hackernews.py tests/test_tools/test_hackernews.py
git commit -m "feat: add HackerNews API client"
```

---

### Task 7: Reddit Tool

**Files:**
- Create: `src/youtube_agent/tools/reddit.py`
- Create: `tests/test_tools/test_reddit.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_tools/test_reddit.py
from unittest.mock import MagicMock, patch

from youtube_agent.tools.reddit import fetch_subreddit_trending


def test_fetch_subreddit_trending():
    mock_submission = MagicMock()
    mock_submission.title = "How I got a job in Germany"
    mock_submission.url = "https://reddit.com/r/brdev/123"
    mock_submission.score = 300
    mock_submission.selftext = "Here is my story..."

    with patch("youtube_agent.tools.reddit.praw.Reddit") as mock_reddit_cls:
        mock_reddit = MagicMock()
        mock_reddit_cls.return_value = mock_reddit
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.return_value = [mock_submission]

        results = fetch_subreddit_trending("brdev", limit=5)
        assert len(results) == 1
        assert results[0]["source"] == "reddit"
        assert results[0]["title"] == "How I got a job in Germany"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_tools/test_reddit.py -v
```

- [ ] **Step 3: Implement reddit.py**

```python
# src/youtube_agent/tools/reddit.py
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


def fetch_subreddit_trending(
    subreddit_name: str, limit: int = 10
) -> list[TrendItem]:
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_tools/test_reddit.py -v
```

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/tools/reddit.py tests/test_tools/test_reddit.py
uv run ruff format src/youtube_agent/tools/reddit.py tests/test_tools/test_reddit.py
git add src/youtube_agent/tools/reddit.py tests/test_tools/test_reddit.py
git commit -m "feat: add Reddit API client"
```

---

### Task 8: RSS News Feeds Tool

**Files:**
- Create: `src/youtube_agent/tools/news_feeds.py`
- Create: `tests/test_tools/test_news_feeds.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_tools/test_news_feeds.py
from unittest.mock import patch

from youtube_agent.tools.news_feeds import fetch_feeds


def test_fetch_feeds():
    mock_feed = {
        "entries": [
            {
                "title": "Python 4.0 is here",
                "link": "https://dev.to/python4",
                "summary": "New Python release with exciting features",
            },
            {
                "title": "Rust vs Go in 2026",
                "link": "https://dev.to/rust-go",
                "summary": "Comparing two popular languages",
            },
        ]
    }
    with patch("youtube_agent.tools.news_feeds.feedparser.parse", return_value=mock_feed):
        results = fetch_feeds(["https://dev.to/feed"], limit_per_feed=5)
        assert len(results) == 2
        assert results[0]["source"] == "rss"
        assert results[0]["title"] == "Python 4.0 is here"


def test_fetch_feeds_handles_error():
    with patch("youtube_agent.tools.news_feeds.feedparser.parse", side_effect=Exception("fail")):
        results = fetch_feeds(["https://bad-feed.com/rss"])
        assert results == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_tools/test_news_feeds.py -v
```

- [ ] **Step 3: Implement news_feeds.py**

```python
# src/youtube_agent/tools/news_feeds.py
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_tools/test_news_feeds.py -v
```

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/tools/news_feeds.py tests/test_tools/test_news_feeds.py
uv run ruff format src/youtube_agent/tools/news_feeds.py tests/test_tools/test_news_feeds.py
git add src/youtube_agent/tools/news_feeds.py tests/test_tools/test_news_feeds.py
git commit -m "feat: add RSS feed reader tool"
```

---

### Task 9: Tavily Search Tool

**Files:**
- Create: `src/youtube_agent/tools/tavily_search.py`
- Create: `tests/test_tools/test_tavily_search.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_tools/test_tavily_search.py
from unittest.mock import MagicMock, patch

from youtube_agent.tools.tavily_search import create_tavily_tool, search_web


def test_search_web():
    with patch("youtube_agent.tools.tavily_search.TavilySearch") as mock_tavily_cls:
        mock_tool = MagicMock()
        mock_tool.invoke.return_value = {
            "results": [
                {"url": "https://example.com", "content": "Some content about Python"},
            ]
        }
        mock_tavily_cls.return_value = mock_tool
        create_tavily_tool(max_results=5)
        results = search_web("python tutorials")
        assert len(results) == 1
        assert results[0]["source"] == "https://example.com"
        assert results[0]["tool"] == "tavily"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_tools/test_tavily_search.py -v
```

- [ ] **Step 3: Implement tavily_search.py (same pattern as research-graph)**

```python
# src/youtube_agent/tools/tavily_search.py
from __future__ import annotations

from langchain_tavily import TavilySearch

from youtube_agent.state import ResearchFinding

_tavily_tool: TavilySearch | None = None


def create_tavily_tool(max_results: int = 5) -> TavilySearch:
    global _tavily_tool
    _tavily_tool = TavilySearch(max_results=max_results)
    return _tavily_tool


def _parse_results(query: str, raw) -> list[ResearchFinding]:
    if isinstance(raw, str):
        return [ResearchFinding(query=query, source="tavily", content=raw, tool="tavily")]
    results = raw.get("results", []) if isinstance(raw, dict) else raw
    findings: list[ResearchFinding] = []
    for r in results:
        findings.append(
            ResearchFinding(
                query=query,
                source=r.get("url", "unknown"),
                content=r.get("content", ""),
                tool="tavily",
            )
        )
    return findings


def search_web(query: str, max_results: int = 5) -> list[ResearchFinding]:
    if _tavily_tool is None:
        raise RuntimeError("Tavily tool not initialized. Call create_tavily_tool() first.")
    raw = _tavily_tool.invoke(query)
    return _parse_results(query, raw)[:max_results]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_tools/test_tavily_search.py -v
```

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/tools/tavily_search.py tests/test_tools/test_tavily_search.py
uv run ruff format src/youtube_agent/tools/tavily_search.py tests/test_tools/test_tavily_search.py
git add src/youtube_agent/tools/tavily_search.py tests/test_tools/test_tavily_search.py
git commit -m "feat: add Tavily search tool"
```

---

### Task 10: Playwright Scraper Tool

**Files:**
- Create: `src/youtube_agent/tools/scraper.py`

- [ ] **Step 1: Implement scraper.py (same pattern as research-graph, no test needed — Playwright requires real browser)**

```python
# src/youtube_agent/tools/scraper.py
from __future__ import annotations

from playwright.async_api import Browser, async_playwright

_browser: Browser | None = None
_playwright_instance = None


async def _get_browser() -> Browser:
    global _browser, _playwright_instance
    if _browser is None:
        _playwright_instance = await async_playwright().start()
        _browser = await _playwright_instance.chromium.launch(headless=True)
    return _browser


async def scrape_page(url: str, timeout: int = 10000) -> str:
    try:
        browser = await _get_browser()
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        text = await page.inner_text("body")
        await context.close()
        return text[:5000]
    except Exception as e:
        return f"Error scraping {url}: {e}"


async def close_browser() -> None:
    global _browser, _playwright_instance
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright_instance:
        await _playwright_instance.stop()
        _playwright_instance = None
```

- [ ] **Step 2: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/tools/scraper.py
uv run ruff format src/youtube_agent/tools/scraper.py
git add src/youtube_agent/tools/scraper.py
git commit -m "feat: add Playwright page scraper"
```

---

### Task 11: Display Module

**Files:**
- Create: `src/youtube_agent/display.py`

- [ ] **Step 1: Implement display.py**

```python
# src/youtube_agent/display.py
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

_console = Console()


def get_console() -> Console:
    return _console


def display_header(title: str, thread_id: str, console: Console | None = None) -> None:
    c = console or _console
    c.print(Panel(f"{title}\nThread: {thread_id}", title="YouTube Agent", border_style="blue"))


def display_topics(topics: list[dict], console: Console | None = None) -> None:
    c = console or _console
    table = Table(title="Sugestões de Tópicos", border_style="green")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Título", style="bold")
    table.add_column("Ângulo")
    table.add_column("Interesse", style="magenta")
    for i, topic in enumerate(topics, 1):
        table.add_row(str(i), topic.get("title", ""), topic.get("angle", ""), topic.get("estimated_interest", ""))
    c.print(table)


def display_outline(outline: dict, console: Console | None = None) -> None:
    c = console or _console
    sections = outline.get("sections", [])
    lines = [f"  {i + 1}. {s.get('title', '')} — {s.get('description', '')}" for i, s in enumerate(sections)]
    c.print(Panel("\n".join(lines), title="Roteiro — Estrutura", border_style="green"))


def display_status(status: str, console: Console | None = None) -> None:
    c = console or _console
    c.print(f"\n[bold cyan]{status}[/bold cyan]")


def display_saved(path: str, console: Console | None = None) -> None:
    c = console or _console
    c.print(f"\n[bold green]Salvo em {path}[/bold green]")


def prompt_approval(message: str, console: Console | None = None) -> str:
    c = console or _console
    return c.input(f"\n[bold yellow]? {message}[/bold yellow] ")
```

- [ ] **Step 2: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/display.py
uv run ruff format src/youtube_agent/display.py
git add src/youtube_agent/display.py
git commit -m "feat: add Rich display module"
```

---

### Task 12: Ideation Sub-Graph

**Files:**
- Create: `src/youtube_agent/agents/ideation/trend_scanner.py`
- Create: `src/youtube_agent/agents/ideation/channel_analyzer.py`
- Create: `src/youtube_agent/agents/ideation/topic_generator.py`
- Create: `src/youtube_agent/agents/ideation/graph.py`
- Create: `tests/test_ideation/test_ideation_graph.py`

- [ ] **Step 1: Implement trend_scanner.py**

```python
# src/youtube_agent/agents/ideation/trend_scanner.py
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


async def scan_trends(state: IdeationState, config: AppConfig) -> dict:
    all_trends = []

    # HackerNews
    try:
        hn_trends = await fetch_top_stories(limit=15)
        all_trends.extend(hn_trends)
    except Exception as e:
        logger.warning("HackerNews scan failed: %s", e)

    # Reddit
    try:
        reddit_trends = fetch_multiple_subreddits(config.reddit.subreddits, limit_per_sub=10)
        all_trends.extend(reddit_trends)
    except Exception as e:
        logger.warning("Reddit scan failed: %s", e)

    # RSS feeds
    try:
        rss_trends = fetch_feeds(config.news.feeds, limit_per_feed=10)
        all_trends.extend(rss_trends)
    except Exception as e:
        logger.warning("RSS feed scan failed: %s", e)

    # YouTube trending
    try:
        yt_client = YouTubeClient()
        yt_trends = yt_client.search_trending(
            "software development career", max_results=10
        )
        all_trends.extend(yt_trends)
    except Exception as e:
        logger.warning("YouTube trend scan failed: %s", e)

    return {"trends": all_trends}
```

- [ ] **Step 2: Implement channel_analyzer.py**

```python
# src/youtube_agent/agents/ideation/channel_analyzer.py
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
```

- [ ] **Step 3: Implement topic_generator.py**

```python
# src/youtube_agent/agents/ideation/topic_generator.py
from __future__ import annotations

import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command, interrupt

from youtube_agent.state import IdeationState, TopicSuggestion

TOPIC_PROMPT = """\
Você é um especialista em conteúdo para YouTube focado em tecnologia e carreira \
internacional para desenvolvedores brasileiros.

Dados de tendências coletados:
{trends}

Estatísticas do canal:
{channel_stats}

Vídeos de concorrentes:
{competitor_insights}

Com base nesses dados, sugira 5-10 tópicos para novos vídeos. Para cada tópico, forneça:
1. title: título do vídeo (em português)
2. angle: ângulo/abordagem específica
3. timeliness: por que este tópico é relevante agora
4. estimated_interest: "high", "medium" ou "low"

Foque em temas que ajudem desenvolvedores brasileiros a:
- Conseguir empregos no exterior
- Melhorar habilidades técnicas
- Desenvolver soft-skills
- Entender o mercado internacional de tecnologia

Retorne APENAS um JSON array de objetos, sem outro texto.

JSON response:"""


def _generate_topics(state: IdeationState, llm: BaseChatModel) -> dict:
    trends_text = "\n".join(
        f"- [{t['source']}] {t['title']} (score: {t['score']})"
        for t in state["trends"][:30]
    )
    channel_text = str(state.get("channel_stats") or "Sem dados do canal")
    competitor_text = "\n".join(
        f"- {c['channel_name']}: {c['title']} ({c['views']} views)"
        for c in state.get("competitor_insights", [])[:15]
    )

    prompt = TOPIC_PROMPT.format(
        trends=trends_text,
        channel_stats=channel_text,
        competitor_insights=competitor_text or "Sem dados de concorrentes",
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    topics = json.loads(raw)
    suggestions = [
        TopicSuggestion(
            title=t["title"],
            angle=t["angle"],
            timeliness=t["timeliness"],
            estimated_interest=t["estimated_interest"],
        )
        for t in topics
    ]
    return {"suggested_topics": suggestions}


def _approve_topic(state: IdeationState) -> Command[Literal["__end__"]]:
    decision = interrupt(
        {
            "suggested_topics": state["suggested_topics"],
            "action": "Escolha um tópico pelo número (ou 0 para cancelar):",
        }
    )
    index = decision.get("selected_index", 0)
    if index <= 0 or index > len(state["suggested_topics"]):
        return Command(update={"selected_topic": None}, goto="__end__")
    selected = state["suggested_topics"][index - 1]
    return Command(update={"selected_topic": selected}, goto="__end__")


def create_topic_generator_nodes(llm: BaseChatModel):
    def generate(state: IdeationState) -> dict:
        return _generate_topics(state, llm)

    return generate, _approve_topic
```

- [ ] **Step 4: Implement ideation graph.py**

```python
# src/youtube_agent/agents/ideation/graph.py
from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from youtube_agent.agents.ideation.channel_analyzer import analyze_channel
from youtube_agent.agents.ideation.topic_generator import create_topic_generator_nodes
from youtube_agent.agents.ideation.trend_scanner import scan_trends
from youtube_agent.config import AppConfig
from youtube_agent.state import IdeationState


def create_ideation_graph(llm: BaseChatModel, config: AppConfig) -> StateGraph:
    generate_topics, approve_topic = create_topic_generator_nodes(llm)

    async def _scan(state: IdeationState) -> dict:
        return await scan_trends(state, config)

    def _analyze(state: IdeationState) -> dict:
        return analyze_channel(state, config)

    builder = StateGraph(IdeationState)
    builder.add_node("trend_scanner", _scan)
    builder.add_node("channel_analyzer", _analyze)
    builder.add_node("topic_generator", generate_topics)
    builder.add_node("approve_topic", approve_topic)

    builder.add_edge(START, "trend_scanner")
    builder.add_edge("trend_scanner", "channel_analyzer")
    builder.add_edge("channel_analyzer", "topic_generator")
    builder.add_edge("topic_generator", "approve_topic")
    builder.add_edge("approve_topic", END)

    return builder
```

- [ ] **Step 5: Write test for ideation graph**

```python
# tests/test_ideation/test_ideation_graph.py
from unittest.mock import MagicMock, patch

from youtube_agent.agents.ideation.graph import create_ideation_graph
from youtube_agent.config import AppConfig


def test_ideation_graph_compiles():
    mock_llm = MagicMock()
    config = AppConfig()
    graph = create_ideation_graph(mock_llm, config)
    compiled = graph.compile()
    assert compiled is not None
```

- [ ] **Step 6: Run test**

```bash
uv run pytest tests/test_ideation/test_ideation_graph.py -v
```

- [ ] **Step 7: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/agents/ideation/ tests/test_ideation/
uv run ruff format src/youtube_agent/agents/ideation/ tests/test_ideation/
git add src/youtube_agent/agents/ideation/ tests/test_ideation/
git commit -m "feat: add ideation sub-graph with trend scanning and topic generation"
```

---

### Task 13: Production Sub-Graph

**Files:**
- Create: `src/youtube_agent/agents/production/researcher.py`
- Create: `src/youtube_agent/agents/production/outliner.py`
- Create: `src/youtube_agent/agents/production/writer.py`
- Create: `src/youtube_agent/agents/production/metadata_generator.py`
- Create: `src/youtube_agent/agents/production/graph.py`
- Create: `tests/test_production/test_production_graph.py`

- [ ] **Step 1: Implement researcher.py**

```python
# src/youtube_agent/agents/production/researcher.py
from __future__ import annotations

import asyncio
import logging

from youtube_agent.state import ProductionState
from youtube_agent.tools.scraper import scrape_page
from youtube_agent.tools.tavily_search import search_web

logger = logging.getLogger(__name__)


async def _research_async(state: ProductionState) -> dict:
    topic = state["topic"]
    queries = [
        topic["title"],
        f"{topic['title']} {topic['angle']}",
        f"{topic['title']} tutorial guia",
    ]

    all_findings = []
    for query in queries:
        try:
            results = search_web(query)
            all_findings.extend(results)
            urls_to_scrape = [r["source"] for r in results[:2] if r["source"].startswith("http")]
            for url in urls_to_scrape:
                try:
                    content = await scrape_page(url)
                    if not content.startswith("Error"):
                        all_findings.append(
                            {
                                "query": query,
                                "source": url,
                                "content": content[:3000],
                                "tool": "playwright",
                            }
                        )
                except Exception as e:
                    logger.warning("Scrape failed for '%s': %s", url, e)
        except Exception as e:
            logger.warning("Search failed for '%s': %s", query, e)

    return {"research_findings": all_findings}


async def research_topic(state: ProductionState) -> dict:
    return await _research_async(state)
```

- [ ] **Step 2: Implement outliner.py**

```python
# src/youtube_agent/agents/production/outliner.py
from __future__ import annotations

import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command, interrupt

from youtube_agent.state import ProductionState, VideoOutline

OUTLINER_PROMPT = """\
Você é um roteirista especialista em vídeos de YouTube sobre tecnologia e carreira \
para desenvolvedores brasileiros.

Tópico: {title}
Ângulo: {angle}

Pesquisa realizada:
{research}

Crie uma estrutura detalhada para o vídeo com:
1. sections: lista de seções, cada uma com "title", "description" e "duration" (em minutos)
2. hooks: 2-3 opções de ganchos para a abertura do vídeo
3. estimated_duration: duração total estimada do vídeo

Inclua: introdução com gancho, pontos principais, exemplos práticos, conclusão e CTA.

Retorne APENAS um JSON object, sem outro texto.

JSON response:"""


def _generate_outline(state: ProductionState, llm: BaseChatModel) -> dict:
    research_text = "\n".join(
        f"[{f['tool']}] {f['content'][:500]}" for f in state["research_findings"][:10]
    )
    prompt = OUTLINER_PROMPT.format(
        title=state["topic"]["title"],
        angle=state["topic"]["angle"],
        research=research_text,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    outline = VideoOutline(
        sections=data.get("sections", []),
        hooks=data.get("hooks", []),
        estimated_duration=data.get("estimated_duration", "10-15 min"),
    )
    return {"outline": outline}


def _approve_outline(state: ProductionState) -> Command[Literal["__end__"]]:
    decision = interrupt(
        {
            "outline": state["outline"],
            "action": "Aprovar estrutura? [s/n/editar]",
        }
    )
    if not decision.get("approved", False):
        return Command(update={"outline": None}, goto="__end__")
    return Command(goto="__end__")


def create_outliner_nodes(llm: BaseChatModel):
    def generate(state: ProductionState) -> dict:
        return _generate_outline(state, llm)

    return generate, _approve_outline
```

- [ ] **Step 3: Implement writer.py**

```python
# src/youtube_agent/agents/production/writer.py
from __future__ import annotations

from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command, interrupt

from youtube_agent.state import ProductionState, VideoScript

WRITER_PROMPT = """\
Você é um roteirista de vídeos de YouTube. Escreva um roteiro completo em português \
para o canal "Além do Código", voltado para desenvolvedores brasileiros.

Tópico: {title}
Ângulo: {angle}

Estrutura aprovada:
{outline}

Pesquisa:
{research}

Escreva o roteiro completo incluindo:
- Falas naturais e conversacionais (como se estivesse conversando com o espectador)
- Notas para o apresentador entre [colchetes]
- Indicações de transição entre seções
- Marcações de tempo aproximadas
- CTA para inscrição e comentários

Escreva o roteiro completo abaixo:"""


def _write_script(state: ProductionState, llm: BaseChatModel) -> dict:
    outline_text = "\n".join(
        f"{i + 1}. {s.get('title', '')} ({s.get('duration', '')}): {s.get('description', '')}"
        for i, s in enumerate(state["outline"]["sections"])
    )
    research_text = "\n".join(
        f"- {f['content'][:300]}" for f in state["research_findings"][:8]
    )
    prompt = WRITER_PROMPT.format(
        title=state["topic"]["title"],
        angle=state["topic"]["angle"],
        outline=outline_text,
        research=research_text,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    script = VideoScript(content=content, word_count=len(content.split()))
    return {"script": script}


def _approve_script(state: ProductionState) -> Command[Literal["__end__"]]:
    decision = interrupt(
        {
            "script_preview": state["script"]["content"][:500] + "...",
            "word_count": state["script"]["word_count"],
            "action": "Aprovar roteiro? [s/n]",
        }
    )
    if not decision.get("approved", False):
        return Command(update={"script": None}, goto="__end__")
    return Command(goto="__end__")


def create_writer_nodes(llm: BaseChatModel):
    def write(state: ProductionState) -> dict:
        return _write_script(state, llm)

    return write, _approve_script
```

- [ ] **Step 4: Implement metadata_generator.py**

```python
# src/youtube_agent/agents/production/metadata_generator.py
from __future__ import annotations

import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command, interrupt

from youtube_agent.state import ProductionState, VideoMetadata

METADATA_PROMPT = """\
Você é um especialista em SEO para YouTube em português brasileiro.

Tópico do vídeo: {title}
Ângulo: {angle}
Resumo do roteiro: {script_preview}

Gere metadados otimizados para YouTube:
1. title_options: 3 opções de título (max 60 caracteres cada, em português)
2. description: descrição completa com keywords, timestamps e links úteis
3. tags: 15-20 tags relevantes em português
4. thumbnail_texts: 3 opções de texto curto para thumbnail (max 5 palavras)

Retorne APENAS um JSON object, sem outro texto.

JSON response:"""


def _generate_metadata(state: ProductionState, llm: BaseChatModel) -> dict:
    prompt = METADATA_PROMPT.format(
        title=state["topic"]["title"],
        angle=state["topic"]["angle"],
        script_preview=state["script"]["content"][:500],
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    metadata = VideoMetadata(
        title_options=data.get("title_options", []),
        description=data.get("description", ""),
        tags=data.get("tags", []),
        thumbnail_texts=data.get("thumbnail_texts", []),
    )
    return {"metadata": metadata}


def _approve_metadata(state: ProductionState) -> Command[Literal["__end__"]]:
    decision = interrupt(
        {
            "metadata": state["metadata"],
            "action": "Aprovar metadados? [s/n]",
        }
    )
    if not decision.get("approved", False):
        return Command(update={"metadata": None}, goto="__end__")
    return Command(goto="__end__")


def create_metadata_nodes(llm: BaseChatModel):
    def generate(state: ProductionState) -> dict:
        return _generate_metadata(state, llm)

    return generate, _approve_metadata
```

- [ ] **Step 5: Implement production graph.py**

```python
# src/youtube_agent/agents/production/graph.py
from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from youtube_agent.agents.production.metadata_generator import create_metadata_nodes
from youtube_agent.agents.production.outliner import create_outliner_nodes
from youtube_agent.agents.production.researcher import research_topic
from youtube_agent.agents.production.writer import create_writer_nodes
from youtube_agent.state import ProductionState
from youtube_agent.tools.tavily_search import create_tavily_tool


def create_production_graph(llm: BaseChatModel, output_dir: str = "./output") -> StateGraph:
    create_tavily_tool(max_results=5)
    generate_outline, approve_outline = create_outliner_nodes(llm)
    write_script, approve_script = create_writer_nodes(llm)
    generate_metadata, approve_metadata = create_metadata_nodes(llm)

    builder = StateGraph(ProductionState)
    builder.add_node("researcher", research_topic)
    builder.add_node("outliner", generate_outline)
    builder.add_node("approve_outline", approve_outline)
    builder.add_node("writer", write_script)
    builder.add_node("approve_script", approve_script)
    builder.add_node("metadata_generator", generate_metadata)
    builder.add_node("approve_metadata", approve_metadata)

    builder.add_edge(START, "researcher")
    builder.add_edge("researcher", "outliner")
    builder.add_edge("outliner", "approve_outline")
    builder.add_edge("approve_outline", "writer")
    builder.add_edge("writer", "approve_script")
    builder.add_edge("approve_script", "metadata_generator")
    builder.add_edge("metadata_generator", "approve_metadata")
    builder.add_edge("approve_metadata", END)

    return builder
```

- [ ] **Step 6: Write test**

```python
# tests/test_production/test_production_graph.py
from unittest.mock import MagicMock

from youtube_agent.agents.production.graph import create_production_graph


def test_production_graph_compiles():
    mock_llm = MagicMock()
    graph = create_production_graph(mock_llm)
    compiled = graph.compile()
    assert compiled is not None
```

- [ ] **Step 7: Run test**

```bash
uv run pytest tests/test_production/test_production_graph.py -v
```

- [ ] **Step 8: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/agents/production/ tests/test_production/
uv run ruff format src/youtube_agent/agents/production/ tests/test_production/
git add src/youtube_agent/agents/production/ tests/test_production/
git commit -m "feat: add production sub-graph with researcher, outliner, writer, metadata"
```

---

### Task 14: Analytics Sub-Graph

**Files:**
- Create: `src/youtube_agent/agents/analytics/data_fetcher.py`
- Create: `src/youtube_agent/agents/analytics/analyzer.py`
- Create: `src/youtube_agent/agents/analytics/strategist.py`
- Create: `src/youtube_agent/agents/analytics/graph.py`
- Create: `tests/test_analytics/test_analytics_graph.py`

- [ ] **Step 1: Implement data_fetcher.py**

```python
# src/youtube_agent/agents/analytics/data_fetcher.py
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
```

- [ ] **Step 2: Implement analyzer.py**

```python
# src/youtube_agent/agents/analytics/analyzer.py
from __future__ import annotations

import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from youtube_agent.state import AnalysisReport, AnalyticsState

ANALYZER_PROMPT = """\
Você é um analista de dados especializado em YouTube. Analise os seguintes dados \
do canal "Além do Código" e de concorrentes.

Vídeos do canal:
{channel_videos}

Vídeos de concorrentes:
{competitor_videos}

Forneça uma análise com:
1. top_performing: IDs e títulos dos 5 vídeos com melhor desempenho
2. bottom_performing: IDs e títulos dos 5 vídeos com pior desempenho
3. patterns: padrões identificados (temas, títulos, duração que funcionam)
4. competitor_comparison: como o canal se compara aos concorrentes

Retorne APENAS um JSON object com essas 4 chaves. \
Para top_performing e bottom_performing, use arrays de objects com video_id, title, views, likes, comments, published_at, channel_id.

JSON response:"""


def _analyze(state: AnalyticsState, llm: BaseChatModel) -> dict:
    channel_text = "\n".join(
        f"- {v['title']} | views: {v['views']} | likes: {v['likes']} | comments: {v['comments']} | {v['published_at']}"
        for v in state["channel_videos"]
    )
    competitor_text = "\n".join(
        f"- {v['title']} | views: {v['views']} | likes: {v['likes']} | {v['published_at']}"
        for v in state.get("competitor_videos", [])[:20]
    )
    prompt = ANALYZER_PROMPT.format(
        channel_videos=channel_text or "Sem dados",
        competitor_videos=competitor_text or "Sem dados de concorrentes",
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    report = AnalysisReport(
        top_performing=data.get("top_performing", []),
        bottom_performing=data.get("bottom_performing", []),
        patterns=data.get("patterns", ""),
        competitor_comparison=data.get("competitor_comparison", ""),
    )
    return {"analysis": report}


def create_analyzer_node(llm: BaseChatModel):
    def analyze(state: AnalyticsState) -> dict:
        return _analyze(state, llm)

    return analyze
```

- [ ] **Step 3: Implement strategist.py**

```python
# src/youtube_agent/agents/analytics/strategist.py
from __future__ import annotations

import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command, interrupt

from youtube_agent.state import AnalyticsState, StrategyReport

STRATEGIST_PROMPT = """\
Você é um estrategista de conteúdo para YouTube, especializado em canais de tecnologia \
voltados para desenvolvedores brasileiros que buscam carreiras internacionais.

Análise do canal:
Padrões: {patterns}
Comparação com concorrentes: {competitor_comparison}

Com base nessa análise, crie uma estratégia com:
1. content_suggestions: sugestões de conteúdo (tipos de vídeo, temas a explorar mais)
2. title_patterns: padrões de título que funcionam melhor
3. posting_recommendations: frequência e melhores horários para postar
4. growth_opportunities: oportunidades de crescimento baseadas em lacunas dos concorrentes

Escreva tudo em português, de forma prática e acionável.

Retorne APENAS um JSON object com essas 4 chaves, valores como strings detalhadas.

JSON response:"""


def _generate_strategy(state: AnalyticsState, llm: BaseChatModel) -> dict:
    prompt = STRATEGIST_PROMPT.format(
        patterns=state["analysis"]["patterns"] if state.get("analysis") else "Sem dados",
        competitor_comparison=state["analysis"]["competitor_comparison"] if state.get("analysis") else "Sem dados",
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    strategy = StrategyReport(
        content_suggestions=data.get("content_suggestions", ""),
        title_patterns=data.get("title_patterns", ""),
        posting_recommendations=data.get("posting_recommendations", ""),
        growth_opportunities=data.get("growth_opportunities", ""),
    )
    return {"strategy": strategy}


def _approve_strategy(state: AnalyticsState) -> Command[Literal["__end__"]]:
    decision = interrupt(
        {
            "strategy": state["strategy"],
            "action": "Estratégia gerada. Revisar? [s/n]",
        }
    )
    return Command(goto="__end__")


def create_strategist_nodes(llm: BaseChatModel):
    def generate(state: AnalyticsState) -> dict:
        return _generate_strategy(state, llm)

    return generate, _approve_strategy
```

- [ ] **Step 4: Implement analytics graph.py**

```python
# src/youtube_agent/agents/analytics/graph.py
from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from youtube_agent.agents.analytics.analyzer import create_analyzer_node
from youtube_agent.agents.analytics.data_fetcher import fetch_data
from youtube_agent.agents.analytics.strategist import create_strategist_nodes
from youtube_agent.config import AppConfig
from youtube_agent.state import AnalyticsState


def create_analytics_graph(llm: BaseChatModel, config: AppConfig) -> StateGraph:
    analyze = create_analyzer_node(llm)
    generate_strategy, approve_strategy = create_strategist_nodes(llm)

    def _fetch(state: AnalyticsState) -> dict:
        return fetch_data(state, config)

    builder = StateGraph(AnalyticsState)
    builder.add_node("data_fetcher", _fetch)
    builder.add_node("analyzer", analyze)
    builder.add_node("strategist", generate_strategy)
    builder.add_node("approve_strategy", approve_strategy)

    builder.add_edge(START, "data_fetcher")
    builder.add_edge("data_fetcher", "analyzer")
    builder.add_edge("analyzer", "strategist")
    builder.add_edge("strategist", "approve_strategy")
    builder.add_edge("approve_strategy", END)

    return builder
```

- [ ] **Step 5: Write test**

```python
# tests/test_analytics/test_analytics_graph.py
from unittest.mock import MagicMock

from youtube_agent.agents.analytics.graph import create_analytics_graph
from youtube_agent.config import AppConfig


def test_analytics_graph_compiles():
    mock_llm = MagicMock()
    config = AppConfig()
    graph = create_analytics_graph(mock_llm, config)
    compiled = graph.compile()
    assert compiled is not None
```

- [ ] **Step 6: Run test**

```bash
uv run pytest tests/test_analytics/test_analytics_graph.py -v
```

- [ ] **Step 7: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/agents/analytics/ tests/test_analytics/
uv run ruff format src/youtube_agent/agents/analytics/ tests/test_analytics/
git add src/youtube_agent/agents/analytics/ tests/test_analytics/
git commit -m "feat: add analytics sub-graph with data fetcher, analyzer, strategist"
```

---

### Task 15: Parent Orchestrator Graph

**Files:**
- Create: `src/youtube_agent/graph.py`

- [ ] **Step 1: Implement graph.py**

```python
# src/youtube_agent/graph.py
from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from youtube_agent.agents.analytics.graph import create_analytics_graph
from youtube_agent.agents.ideation.graph import create_ideation_graph
from youtube_agent.agents.production.graph import create_production_graph
from youtube_agent.config import AppConfig
from youtube_agent.llm import create_llm
from youtube_agent.state import OrchestratorState


def _route_by_mode(state: OrchestratorState) -> Literal["ideation", "production", "analytics"]:
    mode = state.get("mode", "full")
    if mode == "ideate":
        return "ideation"
    if mode == "produce":
        return "production"
    if mode == "analyze":
        return "analytics"
    return "ideation"  # "full" starts with ideation


def _after_ideation(state: OrchestratorState) -> Literal["prepare_production", "__end__"]:
    if state.get("mode") == "ideate":
        return END
    if state.get("selected_topic"):
        return "prepare_production"
    return END


def _after_production(state: OrchestratorState) -> Literal["__end__"]:
    return END


def create_orchestrator_graph(
    config: AppConfig,
    checkpointer: BaseCheckpointSaver | None = None,
) -> Any:
    llm = create_llm(config.llm)
    retry = RetryPolicy(max_attempts=3, initial_interval=1.0)

    ideation = create_ideation_graph(llm, config).compile()
    production = create_production_graph(llm, output_dir=config.output.dir).compile()
    analytics = create_analytics_graph(llm, config).compile()

    def _map_ideation_to_production(state: OrchestratorState) -> dict:
        """Map selected_topic from ideation into topic for production."""
        return {"topic": state["selected_topic"]}

    builder = StateGraph(OrchestratorState)
    builder.add_node("ideation", ideation, retry_policy=retry)
    builder.add_node("prepare_production", _map_ideation_to_production)
    builder.add_node("production", production, retry_policy=retry)
    builder.add_node("analytics", analytics, retry_policy=retry)

    builder.add_conditional_edges(START, _route_by_mode, ["ideation", "production", "analytics"])
    builder.add_conditional_edges("ideation", _after_ideation, ["prepare_production", END])
    builder.add_edge("prepare_production", "production")
    builder.add_conditional_edges("production", _after_production, [END])
    builder.add_edge("analytics", END)

    return builder.compile(checkpointer=checkpointer)
```

- [ ] **Step 2: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/graph.py
uv run ruff format src/youtube_agent/graph.py
git add src/youtube_agent/graph.py
git commit -m "feat: add parent orchestrator graph"
```

---

### Task 16: CLI

**Files:**
- Create: `src/youtube_agent/cli.py`

- [ ] **Step 1: Implement cli.py**

```python
# src/youtube_agent/cli.py
from __future__ import annotations

import uuid

import click
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from rich.console import Console

from youtube_agent.config import load_config
from youtube_agent.display import (
    display_header,
    display_outline,
    display_saved,
    display_status,
    display_topics,
    prompt_approval,
)
from youtube_agent.graph import create_orchestrator_graph

console = Console()


def _get_checkpointer(config):
    if config.persistence.backend == "postgres":
        from langgraph.checkpoint.postgres import PostgresSaver

        return PostgresSaver.from_conn_string(config.persistence.postgres_url)
    return SqliteSaver.from_conn_string(config.persistence.sqlite_path)


def _handle_interrupt(interrupt_data: dict) -> dict:
    action = interrupt_data.get("action", "")

    if "suggested_topics" in interrupt_data:
        display_topics(interrupt_data["suggested_topics"])
        choice = prompt_approval(action)
        try:
            index = int(choice)
        except ValueError:
            index = 0
        return {"selected_index": index}

    if "outline" in interrupt_data:
        display_outline(interrupt_data["outline"])
        choice = prompt_approval(action)
        return {"approved": choice.lower() in ("s", "sim", "y", "yes")}

    if "script_preview" in interrupt_data:
        console.print(f"\n[dim]{interrupt_data['script_preview']}[/dim]")
        console.print(f"[cyan]Palavras: {interrupt_data.get('word_count', '?')}[/cyan]")
        choice = prompt_approval(action)
        return {"approved": choice.lower() in ("s", "sim", "y", "yes")}

    if "metadata" in interrupt_data:
        metadata = interrupt_data["metadata"]
        console.print("\n[bold]Títulos:[/bold]")
        for i, t in enumerate(metadata.get("title_options", []), 1):
            console.print(f"  {i}. {t}")
        console.print(f"\n[bold]Tags:[/bold] {', '.join(metadata.get('tags', []))}")
        console.print(f"\n[bold]Thumbnail:[/bold] {metadata.get('thumbnail_texts', [])}")
        choice = prompt_approval(action)
        return {"approved": choice.lower() in ("s", "sim", "y", "yes")}

    if "strategy" in interrupt_data:
        strategy = interrupt_data["strategy"]
        for key, value in strategy.items():
            console.print(f"\n[bold]{key}:[/bold] {value}")
        prompt_approval(action)
        return {}

    choice = prompt_approval(action)
    return {"approved": choice.lower() in ("s", "sim", "y", "yes")}


def _run_graph(graph, input_state: dict, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    for chunk in graph.stream(input_state, config, stream_mode="updates", subgraphs=True):
        namespace, update = chunk
        node_name = list(update.keys())[0] if update else "unknown"
        display_status(f"▶ {node_name}")

    while True:
        state = graph.get_state(config, subgraphs=True)
        if not state.tasks:
            break
        has_interrupts = False
        for task in state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                has_interrupts = True
                for intr in task.interrupts:
                    resume_value = _handle_interrupt(intr.value)
                    for chunk in graph.stream(
                        Command(resume=resume_value), config, stream_mode="updates", subgraphs=True
                    ):
                        namespace, update = chunk
                        node_name = list(update.keys())[0] if update else "unknown"
                        display_status(f"▶ {node_name}")
        if not has_interrupts:
            break


def _handle_resume(graph, thread_id: str):
    """Resume a paused session by entering the interrupt handling loop directly."""
    config = {"configurable": {"thread_id": thread_id}}
    while True:
        state = graph.get_state(config, subgraphs=True)
        if not state.tasks:
            break
        has_interrupts = False
        for task in state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                has_interrupts = True
                for intr in task.interrupts:
                    resume_value = _handle_interrupt(intr.value)
                    for chunk in graph.stream(
                        Command(resume=resume_value), config, stream_mode="updates", subgraphs=True
                    ):
                        namespace, update = chunk
                        node_name = list(update.keys())[0] if update else "unknown"
                        display_status(f"▶ {node_name}")
        if not has_interrupts:
            break


@click.group()
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
@click.pass_context
def cli(ctx, config_path):
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config_path)


@cli.command()
@click.pass_context
def ideate(ctx):
    """Run content ideation pipeline."""
    config = ctx.obj["config"]
    thread_id = str(uuid.uuid4())
    checkpointer = _get_checkpointer(config)
    graph = create_orchestrator_graph(config, checkpointer=checkpointer)
    display_header("Ideação de Conteúdo", thread_id)
    _run_graph(graph, {"mode": "ideate"}, thread_id)


@cli.command()
@click.option("--topic", default=None, help="Topic title for the video")
@click.pass_context
def produce(ctx, topic):
    """Run video production pipeline."""
    config = ctx.obj["config"]
    thread_id = str(uuid.uuid4())
    checkpointer = _get_checkpointer(config)
    graph = create_orchestrator_graph(config, checkpointer=checkpointer)

    if topic:
        input_state = {
            "mode": "produce",
            "selected_topic": {
                "title": topic,
                "angle": "",
                "timeliness": "",
                "estimated_interest": "high",
            },
        }
    else:
        topic_input = console.input("[bold yellow]? Qual o tópico do vídeo?[/bold yellow] ")
        input_state = {
            "mode": "produce",
            "selected_topic": {
                "title": topic_input,
                "angle": "",
                "timeliness": "",
                "estimated_interest": "high",
            },
        }

    display_header("Produção de Vídeo", thread_id)
    _run_graph(graph, input_state, thread_id)


@cli.command()
@click.pass_context
def analyze(ctx):
    """Run channel analytics pipeline."""
    config = ctx.obj["config"]
    thread_id = str(uuid.uuid4())
    checkpointer = _get_checkpointer(config)
    graph = create_orchestrator_graph(config, checkpointer=checkpointer)
    display_header("Análise do Canal", thread_id)
    _run_graph(graph, {"mode": "analyze"}, thread_id)


@cli.command()
@click.pass_context
def full(ctx):
    """Run full pipeline: ideation → production."""
    config = ctx.obj["config"]
    thread_id = str(uuid.uuid4())
    checkpointer = _get_checkpointer(config)
    graph = create_orchestrator_graph(config, checkpointer=checkpointer)
    display_header("Pipeline Completo", thread_id)
    _run_graph(graph, {"mode": "full"}, thread_id)


@cli.command()
@click.argument("thread_id")
@click.pass_context
def resume(ctx, thread_id):
    """Resume an interrupted session."""
    config = ctx.obj["config"]
    checkpointer = _get_checkpointer(config)
    graph = create_orchestrator_graph(config, checkpointer=checkpointer)
    display_header("Retomando Sessão", thread_id)
    # Resume re-enters the interrupt loop with the existing thread
    graph_config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(graph_config, subgraphs=True)
    if not state.tasks:
        console.print("[yellow]Nenhuma sessão pendente encontrada.[/yellow]")
        return
    # Enter the interrupt handling loop — _run_graph handles interrupts
    # Pass None to skip initial stream, go straight to interrupt handling
    _handle_resume(graph, thread_id)


@cli.command()
@click.pass_context
def sessions(ctx):
    """List active/paused sessions."""
    config = ctx.obj["config"]
    checkpointer = _get_checkpointer(config)
    from rich.table import Table
    table = Table(title="Sessões", border_style="blue")
    table.add_column("Thread ID", style="cyan")
    table.add_column("Status")
    table.add_column("Checkpoint")
    for checkpoint_tuple in checkpointer.list(None):
        tid = checkpoint_tuple.config.get("configurable", {}).get("thread_id", "?")
        ts = checkpoint_tuple.checkpoint.get("ts", "?")
        table.add_row(tid, "paused", ts)
    console.print(table)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 2: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/cli.py
uv run ruff format src/youtube_agent/cli.py
git add src/youtube_agent/cli.py
git commit -m "feat: add CLI with ideate, produce, analyze, full, resume commands"
```

---

### Task 17: Output Saving & Shared Utils

**Files:**
- Create: `src/youtube_agent/utils.py`
- Modify: `src/youtube_agent/agents/production/graph.py`
- Modify: `src/youtube_agent/agents/analytics/graph.py`

- [ ] **Step 1: Create shared utils.py**

```python
# src/youtube_agent/utils.py
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:50].rstrip("-")


def get_output_dir(base_dir: str, label: str) -> Path:
    today = date.today().isoformat()
    slug = slugify(label)
    out = Path(base_dir) / f"{today}-{slug}"
    counter = 2
    original = out
    while out.exists():
        out = Path(f"{original}-{counter}")
        counter += 1
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def save_text(path: Path, text: str) -> None:
    path.write_text(text)
```

- [ ] **Step 2: Update production graph.py to save output**

Replace the full `create_production_graph` function:

```python
# src/youtube_agent/agents/production/graph.py
from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from youtube_agent.agents.production.metadata_generator import create_metadata_nodes
from youtube_agent.agents.production.outliner import create_outliner_nodes
from youtube_agent.agents.production.researcher import research_topic
from youtube_agent.agents.production.writer import create_writer_nodes
from youtube_agent.state import ProductionState
from youtube_agent.tools.tavily_search import create_tavily_tool
from youtube_agent.utils import get_output_dir, save_json, save_text


def create_production_graph(llm: BaseChatModel, output_dir: str = "./output") -> StateGraph:
    create_tavily_tool(max_results=5)
    generate_outline, approve_outline = create_outliner_nodes(llm)
    write_script, approve_script = create_writer_nodes(llm)
    generate_metadata, approve_metadata = create_metadata_nodes(llm)

    def _save_output(state: ProductionState) -> dict:
        out = get_output_dir(output_dir, state["topic"]["title"])
        if state.get("script"):
            save_text(out / "script.md", state["script"]["content"])
        if state.get("outline"):
            save_json(out / "outline.json", state["outline"])
        if state.get("metadata"):
            save_json(out / "metadata.json", state["metadata"])
        return {}

    builder = StateGraph(ProductionState)
    builder.add_node("researcher", research_topic)
    builder.add_node("outliner", generate_outline)
    builder.add_node("approve_outline", approve_outline)
    builder.add_node("writer", write_script)
    builder.add_node("approve_script", approve_script)
    builder.add_node("metadata_generator", generate_metadata)
    builder.add_node("approve_metadata", approve_metadata)
    builder.add_node("save_output", _save_output)

    builder.add_edge(START, "researcher")
    builder.add_edge("researcher", "outliner")
    builder.add_edge("outliner", "approve_outline")
    builder.add_edge("approve_outline", "writer")
    builder.add_edge("writer", "approve_script")
    builder.add_edge("approve_script", "metadata_generator")
    builder.add_edge("metadata_generator", "approve_metadata")
    builder.add_edge("approve_metadata", "save_output")
    builder.add_edge("save_output", END)

    return builder
```

- [ ] **Step 3: Update analytics graph.py to save strategy report**

Add a `_save_report` node to the analytics graph after `approve_strategy`:

```python
# Add to analytics/graph.py

from youtube_agent.utils import get_output_dir, save_text


def create_analytics_graph(llm: BaseChatModel, config: AppConfig) -> StateGraph:
    analyze = create_analyzer_node(llm)
    generate_strategy, approve_strategy = create_strategist_nodes(llm)

    def _fetch(state: AnalyticsState) -> dict:
        return fetch_data(state, config)

    def _save_report(state: AnalyticsState) -> dict:
        if state.get("strategy"):
            out = get_output_dir(config.output.dir, "analytics-report")
            report = "\n\n".join(
                f"## {k}\n{v}" for k, v in state["strategy"].items()
            )
            save_text(out / "strategy.md", report)
        if state.get("analysis"):
            # analysis already in the output dir from strategy
            pass
        return {}

    builder = StateGraph(AnalyticsState)
    builder.add_node("data_fetcher", _fetch)
    builder.add_node("analyzer", analyze)
    builder.add_node("strategist", generate_strategy)
    builder.add_node("approve_strategy", approve_strategy)
    builder.add_node("save_report", _save_report)

    builder.add_edge(START, "data_fetcher")
    builder.add_edge("data_fetcher", "analyzer")
    builder.add_edge("analyzer", "strategist")
    builder.add_edge("strategist", "approve_strategy")
    builder.add_edge("approve_strategy", "save_report")
    builder.add_edge("save_report", END)

    return builder
```

- [ ] **Step 4: Update parent orchestrator to pass output_dir to production**

In `src/youtube_agent/graph.py`, update:
```python
production = create_production_graph(llm, output_dir=config.output.dir).compile()
```

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check --fix src/youtube_agent/utils.py src/youtube_agent/agents/production/graph.py src/youtube_agent/agents/analytics/graph.py src/youtube_agent/graph.py
uv run ruff format src/youtube_agent/utils.py src/youtube_agent/agents/production/graph.py src/youtube_agent/agents/analytics/graph.py src/youtube_agent/graph.py
git add src/youtube_agent/utils.py src/youtube_agent/agents/production/graph.py src/youtube_agent/agents/analytics/graph.py src/youtube_agent/graph.py
git commit -m "feat: add output saving for production and analytics pipelines"
```

---

### Task 18: Orchestrator and CLI Tests

**Files:**
- Create: `tests/test_graph.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write orchestrator test**

```python
# tests/test_graph.py
from unittest.mock import MagicMock, patch

from youtube_agent.config import AppConfig
from youtube_agent.graph import create_orchestrator_graph


@patch("youtube_agent.graph.create_llm")
@patch("youtube_agent.graph.create_ideation_graph")
@patch("youtube_agent.graph.create_production_graph")
@patch("youtube_agent.graph.create_analytics_graph")
def test_orchestrator_compiles(mock_analytics, mock_prod, mock_ideation, mock_llm):
    mock_llm.return_value = MagicMock()
    # Each create_*_graph returns a StateGraph with .compile()
    for mock_graph in [mock_ideation, mock_prod, mock_analytics]:
        mock_builder = MagicMock()
        mock_builder.compile.return_value = MagicMock()
        mock_graph.return_value = mock_builder

    config = AppConfig()
    graph = create_orchestrator_graph(config)
    assert graph is not None


@patch("youtube_agent.graph.create_llm")
@patch("youtube_agent.graph.create_ideation_graph")
@patch("youtube_agent.graph.create_production_graph")
@patch("youtube_agent.graph.create_analytics_graph")
def test_route_by_mode_ideate(mock_analytics, mock_prod, mock_ideation, mock_llm):
    from youtube_agent.graph import _route_by_mode
    state = {"selected_topic": None, "mode": "ideate"}
    assert _route_by_mode(state) == "ideation"

    state = {"selected_topic": None, "mode": "analyze"}
    assert _route_by_mode(state) == "analytics"

    state = {"selected_topic": None, "mode": "full"}
    assert _route_by_mode(state) == "ideation"
```

- [ ] **Step 2: Write CLI test**

```python
# tests/test_cli.py
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from youtube_agent.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "ideate" in result.output
    assert "produce" in result.output
    assert "analyze" in result.output
    assert "full" in result.output
    assert "resume" in result.output
    assert "sessions" in result.output


def test_ideate_command_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["ideate", "--help"])
    assert result.exit_code == 0
    assert "ideation" in result.output.lower()
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/test_graph.py tests/test_cli.py -v
```

- [ ] **Step 4: Lint and commit**

```bash
uv run ruff check --fix tests/test_graph.py tests/test_cli.py
uv run ruff format tests/test_graph.py tests/test_cli.py
git add tests/test_graph.py tests/test_cli.py
git commit -m "test: add orchestrator and CLI tests"
```

---

### Task 19: Run All Tests and Final Lint

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest tests/ -v
```

- [ ] **Step 2: Run full lint**

```bash
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
```

- [ ] **Step 3: Commit any fixes**

```bash
git add -A
git commit -m "chore: fix lint issues across codebase"
```

- [ ] **Step 4: Verify CLI entry point**

```bash
uv run youtube-agent --help
```

Expected: Shows help with `ideate`, `produce`, `analyze`, `full`, `resume`, `sessions` commands.

- [ ] **Step 5: Final commit if needed and push**

```bash
git push -u origin main
```
