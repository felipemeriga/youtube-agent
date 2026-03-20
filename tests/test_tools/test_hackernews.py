from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from youtube_agent.tools.hackernews import fetch_top_stories


@pytest.mark.asyncio
async def test_fetch_top_stories():
    mock_response_ids = MagicMock()
    mock_response_ids.json.return_value = [1, 2]
    mock_response_ids.raise_for_status = MagicMock()

    mock_response_item1 = MagicMock()
    mock_response_item1.json.return_value = {
        "id": 1,
        "title": "Show HN: My Project",
        "url": "https://example.com",
        "score": 200,
        "type": "story",
    }
    mock_response_item1.raise_for_status = MagicMock()

    mock_response_item2 = MagicMock()
    mock_response_item2.json.return_value = {
        "id": 2,
        "title": "Ask HN: Best language?",
        "url": "",
        "score": 150,
        "type": "story",
    }
    mock_response_item2.raise_for_status = MagicMock()

    with patch("youtube_agent.tools.hackernews.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = [
            mock_response_ids,
            mock_response_item1,
            mock_response_item2,
        ]
        results = await fetch_top_stories(limit=2)
        assert len(results) == 2
        assert results[0]["source"] == "hackernews"
        assert results[0]["title"] == "Show HN: My Project"
