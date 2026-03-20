from unittest.mock import MagicMock

from youtube_agent.agents.analytics.graph import create_analytics_graph
from youtube_agent.config import AppConfig


def test_analytics_graph_compiles():
    mock_llm = MagicMock()
    config = AppConfig()
    graph = create_analytics_graph(mock_llm, config)
    compiled = graph.compile()
    assert compiled is not None
    assert "data_fetcher" in graph.nodes
    assert "analyzer" in graph.nodes
    assert "strategist" in graph.nodes
