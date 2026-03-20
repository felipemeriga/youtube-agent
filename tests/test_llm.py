import pytest

from youtube_agent.config import LLMConfig
from youtube_agent.llm import create_llm


def test_create_llm_unsupported_provider():
    config = LLMConfig(provider="unsupported")
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_llm(config)


def test_create_llm_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy")
    config = LLMConfig(provider="openai", model="gpt-4o-mini", temperature=0.3)
    llm = create_llm(config)
    assert llm is not None
