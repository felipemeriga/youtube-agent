from unittest.mock import MagicMock, patch

from youtube_agent.agents.production.graph import create_production_graph


@patch("youtube_agent.agents.production.graph.create_tavily_tool")
def test_production_graph_compiles(mock_tavily):
    mock_llm = MagicMock()
    graph = create_production_graph(
        outliner_llm=mock_llm,
        writer_llm=mock_llm,
        metadata_llm=mock_llm,
    )
    compiled = graph.compile()
    assert compiled is not None
    assert "researcher" in graph.nodes
    assert "outliner" in graph.nodes
    assert "writer" in graph.nodes
    assert "metadata_generator" in graph.nodes
