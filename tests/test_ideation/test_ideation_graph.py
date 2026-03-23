from unittest.mock import MagicMock

from youtube_agent.agents.ideation.graph import create_ideation_graph
from youtube_agent.config import AppConfig


def test_ideation_graph_compiles():
    mock_llm = MagicMock()
    config = AppConfig()
    graph = create_ideation_graph(mock_llm, config)
    compiled = graph.compile()
    assert compiled is not None
    # Verify all expected nodes exist
    assert "trend_scanner" in graph.nodes
    assert "channel_analyzer" in graph.nodes
    assert "topic_generator" in graph.nodes
    assert "approve_topic" in graph.nodes
