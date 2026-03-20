from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from youtube_agent.agents.ideation.channel_analyzer import analyze_channel
from youtube_agent.agents.ideation.topic_generator import create_topic_generator_nodes
from youtube_agent.agents.ideation.trend_scanner import scan_trends
from youtube_agent.config import AppConfig
from youtube_agent.state import IdeationState


def create_ideation_graph(llm: BaseChatModel, config: AppConfig) -> StateGraph:
    generate_topics, approve_topic = create_topic_generator_nodes(llm)

    async def _scan(state: IdeationState) -> dict:
        return await scan_trends(state, config)

    def _analyze(state: IdeationState) -> dict:
        return analyze_channel(state, config)

    builder = StateGraph(IdeationState)
    builder.add_node("trend_scanner", _scan)
    builder.add_node("channel_analyzer", _analyze)
    builder.add_node("topic_generator", generate_topics)
    builder.add_node("approve_topic", approve_topic)

    builder.add_edge(START, "trend_scanner")
    builder.add_edge("trend_scanner", "channel_analyzer")
    builder.add_edge("channel_analyzer", "topic_generator")
    builder.add_edge("topic_generator", "approve_topic")
    builder.add_edge("approve_topic", END)

    return builder
