from unittest.mock import patch

from youtube_agent.tools.news_feeds import fetch_feeds


def test_fetch_feeds():
    mock_feed = {
        "entries": [
            {
                "title": "Python 4.0 is here",
                "link": "https://dev.to/python4",
                "summary": "New Python release",
            },
            {
                "title": "Rust vs Go in 2026",
                "link": "https://dev.to/rust-go",
                "summary": "Comparing languages",
            },
        ]
    }
    with patch("youtube_agent.tools.news_feeds.feedparser.parse", return_value=mock_feed):
        results = fetch_feeds(["https://dev.to/feed"], limit_per_feed=5)
        assert len(results) == 2
        assert results[0]["source"] == "rss"
        assert results[0]["title"] == "Python 4.0 is here"


def test_fetch_feeds_handles_error():
    with patch("youtube_agent.tools.news_feeds.feedparser.parse", side_effect=Exception("fail")):
        results = fetch_feeds(["https://bad-feed.com/rss"])
        assert results == []
