from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from youtube_agent.agents.analytics.graph import create_analytics_graph
from youtube_agent.agents.ideation.graph import create_ideation_graph
from youtube_agent.agents.production.graph import create_production_graph
from youtube_agent.config import AppConfig
from youtube_agent.llm import create_llm
from youtube_agent.state import OrchestratorState


def _route_by_mode(
    state: OrchestratorState,
) -> Literal["ideation", "production", "prepare_analytics"]:
    mode = state.get("mode", "full")
    if mode == "ideate":
        return "ideation"
    if mode == "produce":
        return "production"
    if mode == "analyze":
        return "prepare_analytics"
    return "ideation"


def _after_ideation(state: OrchestratorState) -> Literal["prepare_production", "__end__"]:
    if state.get("mode") == "ideate":
        return END
    if state.get("selected_topic"):
        return "prepare_production"
    return END


def _after_production(
    state: OrchestratorState,
) -> Literal["prepare_analytics", "__end__"]:
    if state.get("mode") == "full":
        return "prepare_analytics"
    return END


def create_orchestrator_graph(
    config: AppConfig,
    checkpointer: BaseCheckpointSaver | None = None,
) -> Any:
    llm = create_llm(config.llm)
    retry = RetryPolicy(max_attempts=3, initial_interval=1.0)

    ideation = create_ideation_graph(llm, config).compile()
    production = create_production_graph(llm, output_dir=config.output.dir).compile()
    analytics = create_analytics_graph(llm, config).compile()

    def _map_ideation_to_production(state: OrchestratorState) -> dict:
        return {"topic": state["selected_topic"]}

    def _map_to_analytics(state: OrchestratorState) -> dict:
        topic = state.get("selected_topic") or state.get("topic")
        topic_context = ""
        if topic:
            topic_context = f"{topic['title']} — {topic.get('angle', '')}"
        elif state.get("prompt"):
            topic_context = state["prompt"]
        return {"topic_context": topic_context}

    builder = StateGraph(OrchestratorState)
    builder.add_node("ideation", ideation, retry_policy=retry)
    builder.add_node("prepare_production", _map_ideation_to_production)
    builder.add_node("production", production, retry_policy=retry)
    builder.add_node("prepare_analytics", _map_to_analytics)
    builder.add_node("analytics", analytics, retry_policy=retry)

    builder.add_conditional_edges(
        START, _route_by_mode, ["ideation", "production", "prepare_analytics"]
    )
    builder.add_conditional_edges("ideation", _after_ideation, ["prepare_production", END])
    builder.add_edge("prepare_production", "production")
    builder.add_conditional_edges("production", _after_production, ["prepare_analytics", END])
    builder.add_edge("prepare_analytics", "analytics")
    builder.add_edge("analytics", END)

    return builder.compile(checkpointer=checkpointer)
