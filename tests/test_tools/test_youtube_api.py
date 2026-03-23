from unittest.mock import MagicMock, patch

from youtube_agent.tools.youtube_api import YouTubeClient


def test_youtube_client_init():
    with patch("youtube_agent.tools.youtube_api.build") as mock_build:
        mock_build.return_value = MagicMock()
        client = YouTubeClient(api_key="test-key")
        assert client is not None
        mock_build.assert_called_once_with("youtube", "v3", developerKey="test-key")


def test_get_channel_videos():
    with patch("youtube_agent.tools.youtube_api.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.search.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": {"videoId": "vid1"},
                    "snippet": {
                        "title": "Test Video",
                        "publishedAt": "2026-01-01T00:00:00Z",
                    },
                }
            ]
        }
        mock_service.videos.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "vid1",
                    "snippet": {
                        "title": "Test Video",
                        "publishedAt": "2026-01-01T00:00:00Z",
                    },
                    "statistics": {
                        "viewCount": "1000",
                        "likeCount": "50",
                        "commentCount": "10",
                    },
                }
            ]
        }
        client = YouTubeClient(api_key="test-key")
        videos = client.get_channel_videos("UC123", max_results=5)
        assert len(videos) == 1
        assert videos[0]["title"] == "Test Video"
        assert videos[0]["views"] == 1000
