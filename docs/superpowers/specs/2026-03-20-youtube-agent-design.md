# YouTube Agent — Design Spec

## Overview

A LangGraph-based CLI tool that helps manage the YouTube channel "Além do Código". The agent covers three pipelines: content ideation, video production, and channel analytics. All generated content is in Portuguese; all code is in English.

The architecture follows the same patterns as [research-graph](https://github.com/felipemeriga/research-graph): composed sub-graphs, human-in-the-loop checkpoints, PostgreSQL persistence, and multi-provider LLM support.

## Channel Context

- **Channel**: Além do Código (Portuguese)
- **Audience**: Brazilian software developers seeking international careers
- **Topics**: technology, software development, soft-skills, getting jobs outside Brazil

## Architecture

Three independent sub-graphs composed into a parent orchestrator. Each sub-graph can run independently via CLI commands.

```
┌─────────────────────────────────────────────────────┐
│                  Parent Orchestrator                 │
│                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │ Ideation │──▶│  Production  │──▶│  Analytics   │  │
│  │ SubGraph │   │   SubGraph   │   │  SubGraph    │  │
│  └──────────┘   └──────────────┘   └─────────────┘  │
│                                                     │
│  Each sub-graph can also run independently via CLI   │
└─────────────────────────────────────────────────────┘
```

**CLI commands:**
- `youtube-agent ideate` — run ideation only
- `youtube-agent produce [--topic "topic"]` — run production pipeline (topic via flag or interactive prompt)
- `youtube-agent analyze` — run analytics only
- `youtube-agent full` — run ideation → production (analytics runs independently)
- `youtube-agent resume [thread_id]` — resume an interrupted run from its last checkpoint
- `youtube-agent sessions` — list active/paused sessions with their checkpoint status

## Shared Patterns (from research-graph)

- `StateGraph` with reducer operators (`operator.add`)
- `interrupt()` for human-in-the-loop checkpoints
- `Command(update + goto)` for state mutations with routing
- `Command(resume)` to restart from interruption points
- Checkpoint persistence: `SqliteSaver` for local dev (default), `PostgresSaver` for production (configurable)
- Multi-provider LLM factory (OpenAI, Anthropic, Google)
- Config via `config.yaml` + `.env`
- Rich terminal UI with streaming output

## Parent Orchestrator State

The parent graph maps state between sub-graphs:

```python
class OrchestratorState(TypedDict):
    selected_topic: TopicSuggestion  # from Ideation → Production
    mode: str  # "ideate", "produce", "analyze", "full"
```

When running `full`, the orchestrator passes `IdeationState.selected_topic` into `ProductionState.topic`. Analytics runs independently (no dependency on Production output).

When running `produce` standalone, the topic is provided via `--topic` CLI flag or interactive prompt.

## Error Handling

- **External API failures** (YouTube, Reddit, HackerNews, RSS): log warning, skip that source, continue with remaining data. The pipeline degrades gracefully — partial trend data is still useful.
- **LLM failures**: retry with exponential backoff (via LangGraph `RetryPolicy`). After 3 retries, halt and inform the user.
- **YouTube API quota**: the tool tracks quota usage per session. If approaching the daily limit (10,000 units), warn the user and skip non-essential API calls.

## Sub-Graph 1: Ideation

Discovers trends and suggests video topics.

```
Trend Scanner ──▶ Channel Analyzer ──▶ Topic Generator (checkpoint)
```

### Nodes

**Trend Scanner** — runs data collection in parallel:
- HackerNews API (`/topstories`, `/beststories`)
- Reddit API (r/brdev, r/cscareerquestions, r/ExperiencedDevs)
- Tech news via RSS feeds (InfoQ, dev.to, TechCrunch) — using `feedparser`
- YouTube Data API v3 — trending videos in tech/career niche

Output: list of trending topics with source and engagement metrics.

**Channel Analyzer** — uses YouTube Data API v3:
- Fetches recent video stats (views, likes, comments)
- Identifies best-performing topics/formats
- Checks competitor channels' recent content

Output: channel performance summary + competitor insights.

**Topic Generator** — LLM-powered:
- Combines trend data + channel analysis
- Generates 5-10 ranked topic suggestions for the target audience
- Each suggestion: title idea, angle, timeliness rationale, estimated interest
- **Checkpoint**: user picks which topic(s) to pursue
- All output in Portuguese

### State

```python
class IdeationState(TypedDict):
    trends: Annotated[list[TrendItem], operator.add]
    channel_stats: ChannelStats
    competitor_insights: list[CompetitorVideo]
    suggested_topics: list[TopicSuggestion]
    selected_topic: TopicSuggestion  # set after checkpoint
```

## Sub-Graph 2: Production

Takes a selected topic and produces a full video content package.

```
Researcher ──▶ Outliner (checkpoint) ──▶ Writer (checkpoint) ──▶ Metadata Generator (checkpoint)
```

### Nodes

**Researcher** — deep-dives into the selected topic:
- Web searches via Tavily
- Page scraping with Playwright
- Gathers data, statistics, examples

Output: structured research findings.

**Outliner** — LLM-powered:
- Creates section-by-section outline (intro, main points, conclusion, CTA)
- Suggests hooks and storytelling angles for Portuguese-speaking audience
- **Checkpoint**: user approves/edits outline

Output: approved outline.

**Writer** — LLM-powered:
- Writes conversational script in Portuguese
- Follows approved outline
- Includes speaker notes, transition cues, timestamps
- **Checkpoint**: user reviews/edits script

Output: approved script.

**Metadata Generator** — LLM-powered:
- Title options (Portuguese, SEO-optimized)
- Description with keywords and links
- Tags list
- Thumbnail text suggestions
- **Checkpoint**: final review

Output: complete metadata package.

### State

```python
class ProductionState(TypedDict):
    topic: TopicSuggestion
    research_findings: Annotated[list[ResearchFinding], operator.add]
    outline: VideoOutline
    script: VideoScript
    metadata: VideoMetadata
```

All outputs saved to disk as markdown in `output/YYYY-MM-DD-topic-name/`. If a directory already exists, a counter suffix is appended (e.g., `output/2026-03-20-topic-name-2/`).

## Sub-Graph 3: Analytics

Analyzes channel performance and provides strategic recommendations.

```
Data Fetcher ──▶ Analyzer ──▶ Strategist (checkpoint)
```

### Nodes

**Data Fetcher** — YouTube Data API v3:
- Recent videos from your channel (configurable count)
- Per-video stats: views, likes, comments, publish date
- Competitor channels' recent videos and stats

Output: raw data collections.

**Analyzer** — LLM-powered:
- Identifies top/bottom performing videos and patterns
- Compares metrics against competitors
- Detects trends (growing/declining topics, title patterns)

Output: structured analysis report.

**Strategist** — LLM-powered:
- Content strategy suggestions
- Title/thumbnail patterns that drive clicks
- Posting frequency and timing recommendations
- Growth opportunities from competitor gaps
- **Checkpoint**: user reviews strategy report
- All output in Portuguese

Output: saved to disk as markdown.

### State

```python
class AnalyticsState(TypedDict):
    channel_videos: list[VideoData]
    competitor_videos: list[VideoData]
    analysis: AnalysisReport
    strategy: StrategyReport
```

## Project Structure

```
youtube-agent/
├── src/
│   └── youtube_agent/
│       ├── __init__.py
│       ├── state.py              # Shared state types
│       ├── graph.py              # Parent orchestrator graph
│       ├── cli.py                # CLI entry point with Rich UI
│       ├── config.py             # YAML + .env config loader
│       ├── llm.py                # Multi-provider LLM factory
│       ├── display.py            # Rich terminal formatting
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── ideation/
│       │   │   ├── __init__.py
│       │   │   ├── graph.py
│       │   │   ├── trend_scanner.py
│       │   │   ├── channel_analyzer.py
│       │   │   └── topic_generator.py
│       │   ├── production/
│       │   │   ├── __init__.py
│       │   │   ├── graph.py
│       │   │   ├── researcher.py
│       │   │   ├── outliner.py
│       │   │   ├── writer.py
│       │   │   └── metadata_generator.py
│       │   └── analytics/
│       │       ├── __init__.py
│       │       ├── graph.py
│       │       ├── data_fetcher.py
│       │       ├── analyzer.py
│       │       └── strategist.py
│       └── tools/
│           ├── __init__.py
│           ├── youtube_api.py    # YouTube Data API v3 wrapper
│           ├── hackernews.py     # HN API client
│           ├── reddit.py         # Reddit API client
│           ├── news_feeds.py     # RSS feed reader
│           ├── tavily_search.py  # Web search via Tavily
│           └── scraper.py        # Playwright page scraper
├── config.yaml
├── .env.example
├── .gitignore                    # Includes output/, .env, *.db
├── pyproject.toml
├── tests/
│   ├── __init__.py
│   ├── test_ideation/
│   ├── test_production/
│   ├── test_analytics/
│   └── test_tools/
└── output/                       # Generated content (gitignored)
```

## Dependencies

**Core:**
- `langgraph`, `langchain-core`, `langchain-openai`, `langchain-anthropic`, `langchain-google-genai`
- `tavily-python`, `playwright`
- `google-api-python-client` (YouTube Data API v3)
- `praw` (Reddit API)
- `httpx` (HackerNews, news scraping)
- `pydantic`
- `rich`
- `aiosqlite` (SQLite checkpointing, default)
- `psycopg2` (PostgreSQL checkpointing, optional)
- `feedparser` (RSS feeds)
- `pyyaml`, `python-dotenv`

**Dev:**
- `uv` (package management)
- `ruff` (linting/formatting)
- `pytest` (testing)

## Configuration

`config.yaml` manages:
- LLM provider and model selection
- YouTube channel ID and competitor channel IDs
- Reddit subreddits to monitor
- News sources to scrape
- Output directory path
- Number of videos to analyze
- PostgreSQL connection for checkpointing

`.env` holds API keys:
- `YOUTUBE_API_KEY`
- `TAVILY_API_KEY`
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY`
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`
- `DATABASE_URL` (optional — only needed if using PostgreSQL instead of SQLite)

## Constraints

- Generated content (output/) is never committed to git
- All generated content in Portuguese
- All code and documentation in English
- Follows conventional commits (`feat:`, `fix:`, `refactor:`, `chore:`)
- Never commit directly to main
- Atomic commits per change
