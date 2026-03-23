# YouTube Agent

AI-powered content pipeline for YouTube channels. Automates the full workflow from trend discovery to script generation, using LangGraph with composed sub-graphs and human-in-the-loop checkpoints.

Built for the **Além do Código** channel but configurable for any YouTube creator.

## What it does

```
Trends (HackerNews, Reddit, RSS, YouTube)
        │
        ▼
   Topic Generation ──► [you pick a topic]
        │
        ▼
   Web Research (Tavily + Playwright)
        │
        ▼
   Outline ──► [you approve]
        │
        ▼
   Script ──► [you approve]
        │
        ▼
   SEO Metadata ──► [you approve]
        │
        ▼
   Saved to ./output/
```

Every step that produces content pauses for your approval before continuing.

## Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL database (Supabase works great)
- Playwright browsers installed

### Installation

```bash
git clone https://github.com/felipemeriga/youtube-agent.git
cd youtube-agent
uv sync
uv run playwright install
```

### Environment variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | At least one LLM provider | OpenAI API key |
| `ANTHROPIC_API_KEY` | At least one LLM provider | Anthropic API key |
| `GOOGLE_API_KEY` | At least one LLM provider | Google AI API key |
| `YOUTUBE_API_KEY` | Yes | YouTube Data API v3 key |
| `TAVILY_API_KEY` | Yes | Tavily search API key |
| `SUPABASE_DB_URL` | Yes | PostgreSQL connection string for checkpointing |

### Configuration

Edit `config.yaml` to set your channel, competitors, and model preferences:

```yaml
llm:
  provider: "openai"
  model: "gpt-4o-mini"
  temperature: 0.3

# Per-node model overrides — use stronger models where quality matters
models:
  writer:
    provider: "openai"
    model: "gpt-4.1"
    temperature: 0.5
  outliner:
    provider: "openai"
    model: "gpt-4.1"
    temperature: 0.3

youtube:
  channel_id: "YOUR_CHANNEL_ID"
  competitor_channel_ids:
    - "COMPETITOR_CHANNEL_ID"
  max_videos: 20

reddit:
  subreddits:
    - "brdev"
    - "cscareerquestions"

news:
  feeds:
    - "https://dev.to/feed"
    - "https://techcrunch.com/feed/"

output:
  dir: "./output"
```

#### Per-node model configuration

You can assign different LLM providers/models to specific nodes. Nodes without an override fall back to the default `llm` config. Available roles:

| Role | What it does | Recommended |
|---|---|---|
| `topic_generator` | Suggests video topics from trend data | Cheap model (gpt-4o-mini) |
| `outliner` | Creates video structure and hooks | Mid-tier model (gpt-4.1) |
| `writer` | Writes the full script | Best model you can afford |
| `metadata_generator` | Generates SEO titles, tags, description | Cheap model (gpt-4o-mini) |

Supported providers: `openai`, `anthropic`, `google`.

### Persona

Edit `persona.yaml` to define the host's voice, opinions, and style. This is injected into the outliner and writer prompts so scripts sound like you, not generic AI.

```yaml
host:
  name: "Your Name"
  background: "Your background and credentials"

  style:
    tone: "conversational, informal"
    humor: "uses humor naturally"
    approach: "provocative, takes a position"

  opinions:
    tech:
      - "Pro open-source"
      - "AI will replace many jobs"
    philosophy:
      - "Create your own freedom"

  avoid:
    - "Never be neutral"
    - "Never sound like a guru"
```

## Usage

### Ideate — discover topics

Scans trends from HackerNews, Reddit, RSS feeds, and YouTube, then suggests video topics grounded in real data.

```bash
# Explore what's trending
youtube-agent ideate

# Guide ideation with a specific interest
youtube-agent ideate "quero explorar temas de geopolítica e economia"
```

### Produce — generate a script

Takes a topic and runs the full production pipeline: research, outline, script, and SEO metadata.

```bash
youtube-agent produce --topic "Guerra do Irã e o impacto da IA"
```

### Full — ideate + produce

Runs both pipelines end-to-end. Pick a topic from suggestions, then the agent researches and writes the script.

```bash
youtube-agent full "quero um vídeo sobre a guerra do irã e IA"
```

### Resume — continue an interrupted session

Every session is checkpointed to PostgreSQL. If you stop mid-flow, resume with the thread ID:

```bash
youtube-agent resume --thread-id <THREAD_ID>
```

### Sessions — list active sessions

```bash
youtube-agent sessions
```

### Options

```bash
youtube-agent --help              # Show all commands
youtube-agent -v ideate           # Enable debug logging
youtube-agent --config my.yaml    # Use a custom config file
```

## Output

Generated content is saved to the `output/` directory, organized by topic:

```
output/
└── guerra-do-ira-e-o-impacto-da-ia/
    ├── script.md        # Full script with timing, stats, talking points
    ├── outline.json     # Approved video structure
    └── metadata.json    # SEO titles, description, tags, thumbnail texts
```

### Script format

The generated script follows a structured format:

- **Timing table** — section-by-section breakdown with timestamps
- **Stats and data** — key facts with cited sources
- **Study context** — background material for the host to study before recording
- **Talking points** — ready-to-use provocative phrases
- **Full script** — complete dialogue, section by section
- **Verified sources** — all sources with URLs

## Architecture

```
OrchestratorGraph
├── IdeationSubgraph
│   ├── trend_scanner      # HackerNews, Reddit, RSS, YouTube API
│   ├── channel_analyzer   # Your channel stats + competitor top videos
│   ├── topic_generator    # LLM suggests topics from real data
│   └── approve_topic      # Human picks a topic (interrupt)
│
├── prepare_production     # Maps selected topic to production state
│
└── ProductionSubgraph
    ├── researcher         # Tavily search + Playwright scraping
    ├── outliner           # LLM generates video structure
    ├── approve_outline    # Human approves (interrupt)
    ├── writer             # LLM writes full script
    ├── approve_script     # Human approves (interrupt)
    ├── metadata_generator # LLM generates SEO metadata
    ├── approve_metadata   # Human approves (interrupt)
    └── save_output        # Saves artifacts to disk
```

Built with [LangGraph](https://github.com/langchain-ai/langgraph) using composed sub-graphs, `interrupt()` for human-in-the-loop, and PostgresSaver for checkpointing.

## Development

```bash
# Run tests
uv run pytest tests/ -x -q

# Lint and format
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
```

## License

MIT
