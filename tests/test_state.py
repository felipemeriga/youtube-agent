from youtube_agent.state import (
    IdeationState,
    TopicSuggestion,
    TrendItem,
    VideoData,
)


def test_trend_item_creation():
    item = TrendItem(
        title="Python 4.0 Released",
        source="hackernews",
        url="https://example.com",
        score=500,
        summary="New Python version released",
    )
    assert item["title"] == "Python 4.0 Released"
    assert item["source"] == "hackernews"


def test_topic_suggestion_creation():
    topic = TopicSuggestion(
        title="Como conseguir emprego na Europa",
        angle="Guia prático para devs brasileiros",
        timeliness="Alta demanda por devs em Portugal",
        estimated_interest="high",
    )
    assert topic["title"] == "Como conseguir emprego na Europa"


def test_ideation_state_has_required_keys():
    state: IdeationState = {
        "trends": [],
        "channel_stats": None,
        "competitor_insights": [],
        "suggested_topics": [],
        "selected_topic": None,
    }
    assert "trends" in state


def test_video_data_creation():
    video = VideoData(
        video_id="abc123",
        title="Test Video",
        views=1000,
        likes=50,
        comments=10,
        published_at="2026-01-01",
        channel_id="UC123",
    )
    assert video["views"] == 1000
