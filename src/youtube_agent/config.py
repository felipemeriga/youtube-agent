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
