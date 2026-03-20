from youtube_agent.graph import _route_by_mode


def test_route_by_mode_ideate():
    state = {"selected_topic": None, "topic": None, "mode": "ideate"}
    assert _route_by_mode(state) == "ideation"


def test_route_by_mode_analyze():
    state = {"selected_topic": None, "topic": None, "mode": "analyze"}
    assert _route_by_mode(state) == "analytics"


def test_route_by_mode_full():
    state = {"selected_topic": None, "topic": None, "mode": "full"}
    assert _route_by_mode(state) == "ideation"


def test_route_by_mode_produce():
    state = {"selected_topic": None, "topic": None, "mode": "produce"}
    assert _route_by_mode(state) == "production"
