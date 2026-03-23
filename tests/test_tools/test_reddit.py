from unittest.mock import MagicMock, patch

from youtube_agent.tools.reddit import fetch_subreddit_trending


def test_fetch_subreddit_trending():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "children": [
                {
                    "data": {
                        "title": "How I got a job in Germany",
                        "permalink": "/r/brdev/comments/123/how_i_got_a_job/",
                        "score": 300,
                        "selftext": "Here is my story...",
                        "stickied": False,
                    }
                },
                {
                    "data": {
                        "title": "Stickied post",
                        "permalink": "/r/brdev/comments/456/stickied/",
                        "score": 100,
                        "selftext": "",
                        "stickied": True,
                    }
                },
            ]
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("youtube_agent.tools.reddit.httpx.get", return_value=mock_response):
        results = fetch_subreddit_trending("brdev", limit=5)
        assert len(results) == 1
        assert results[0]["source"] == "reddit"
        assert results[0]["title"] == "How I got a job in Germany"


def test_fetch_subreddit_handles_error():
    with patch("youtube_agent.tools.reddit.httpx.get", side_effect=Exception("network error")):
        results = fetch_subreddit_trending("brdev")
        assert results == []
