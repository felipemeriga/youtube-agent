from unittest.mock import MagicMock, patch

from youtube_agent.tools.reddit import fetch_subreddit_trending


def test_fetch_subreddit_trending():
    mock_submission = MagicMock()
    mock_submission.title = "How I got a job in Germany"
    mock_submission.url = "https://reddit.com/r/brdev/123"
    mock_submission.score = 300
    mock_submission.selftext = "Here is my story..."

    with patch("youtube_agent.tools.reddit.praw.Reddit") as mock_reddit_cls:
        mock_reddit = MagicMock()
        mock_reddit_cls.return_value = mock_reddit
        mock_subreddit = MagicMock()
        mock_reddit.subreddit.return_value = mock_subreddit
        mock_subreddit.hot.return_value = [mock_submission]
        results = fetch_subreddit_trending("brdev", limit=5)
        assert len(results) == 1
        assert results[0]["source"] == "reddit"
        assert results[0]["title"] == "How I got a job in Germany"
