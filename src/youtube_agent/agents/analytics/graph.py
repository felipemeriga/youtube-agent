from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from youtube_agent.agents.analytics.analyzer import create_analyzer_node
from youtube_agent.agents.analytics.data_fetcher import fetch_data
from youtube_agent.agents.analytics.strategist import create_strategist_nodes
from youtube_agent.config import AppConfig
from youtube_agent.state import AnalyticsState


def create_analytics_graph(llm: BaseChatModel, config: AppConfig) -> StateGraph:
    analyze = create_analyzer_node(llm)
    generate_strategy, approve_strategy = create_strategist_nodes(llm)

    def _fetch(state: AnalyticsState) -> dict:
        return fetch_data(state, config)

    builder = StateGraph(AnalyticsState)
    builder.add_node("data_fetcher", _fetch)
    builder.add_node("analyzer", analyze)
    builder.add_node("strategist", generate_strategy)
    builder.add_node("approve_strategy", approve_strategy)

    builder.add_edge(START, "data_fetcher")
    builder.add_edge("data_fetcher", "analyzer")
    builder.add_edge("analyzer", "strategist")
    builder.add_edge("strategist", "approve_strategy")
    builder.add_edge("approve_strategy", END)

    return builder
