from unittest.mock import MagicMock, patch

from youtube_agent.tools.tavily_search import create_tavily_tool, search_web


def test_search_web():
    with patch("youtube_agent.tools.tavily_search.TavilySearch") as mock_tavily_cls:
        mock_tool = MagicMock()
        mock_tool.invoke.return_value = {
            "results": [{"url": "https://example.com", "content": "Some content"}]
        }
        mock_tavily_cls.return_value = mock_tool
        create_tavily_tool(max_results=5)
        results = search_web("python tutorials")
        assert len(results) == 1
        assert results[0]["source"] == "https://example.com"
        assert results[0]["tool"] == "tavily"
