from youtube_agent.config import load_config


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
