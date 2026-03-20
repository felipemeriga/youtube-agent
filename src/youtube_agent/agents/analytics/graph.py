from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from youtube_agent.agents.analytics.analyzer import create_analyzer_node
from youtube_agent.agents.analytics.data_fetcher import fetch_data
from youtube_agent.agents.analytics.strategist import create_strategist_nodes
from youtube_agent.config import AppConfig
from youtube_agent.state import AnalyticsState
from youtube_agent.utils import get_output_dir, save_text


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

    def _save_report(state: AnalyticsState) -> dict:
        if state.get("strategy"):
            out = get_output_dir(config.output.dir, "analytics-report")
            report = "\n\n".join(f"## {k}\n{v}" for k, v in state["strategy"].items())
            save_text(out / "strategy.md", report)
        return {}

    def _route_after_strategy(state: AnalyticsState):
        if state.get("strategy") is None:
            return END
        return "save_report"

    builder.add_node("save_report", _save_report)
    builder.add_conditional_edges("approve_strategy", _route_after_strategy, ["save_report", END])
    builder.add_edge("save_report", END)

    return builder
