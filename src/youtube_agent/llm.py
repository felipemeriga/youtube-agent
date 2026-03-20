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
            f"Unsupported LLM provider: {config.provider}. Supported: {', '.join(_PROVIDERS)}"
        )
    module_name, class_name = _PROVIDERS[config.provider]
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls(model=config.model, temperature=config.temperature)
