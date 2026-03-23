from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from youtube_agent.agents.ideation.graph import create_ideation_graph
from youtube_agent.agents.production.graph import create_production_graph
from youtube_agent.config import AppConfig
from youtube_agent.llm import create_llm
from youtube_agent.state import OrchestratorState


def _route_by_mode(state: OrchestratorState) -> Literal["ideation", "production"]:
    mode = state.get("mode", "full")
    if mode == "produce":
        return "production"
    return "ideation"


def _after_ideation(state: OrchestratorState) -> Literal["prepare_production", "__end__"]:
    if state.get("mode") == "ideate":
        return END
    if state.get("selected_topic"):
        return "prepare_production"
    return END


def create_orchestrator_graph(
    config: AppConfig,
    checkpointer: BaseCheckpointSaver | None = None,
) -> Any:
    llm = create_llm(config.llm)
    retry = RetryPolicy(max_attempts=3, initial_interval=1.0)

    ideation = create_ideation_graph(llm, config).compile()
    production = create_production_graph(llm, output_dir=config.output.dir).compile()

    def _map_ideation_to_production(state: OrchestratorState) -> dict:
        return {"topic": state["selected_topic"]}

    builder = StateGraph(OrchestratorState)
    builder.add_node("ideation", ideation, retry_policy=retry)
    builder.add_node("prepare_production", _map_ideation_to_production)
    builder.add_node("production", production, retry_policy=retry)

    builder.add_conditional_edges(START, _route_by_mode, ["ideation", "production"])
    builder.add_conditional_edges("ideation", _after_ideation, ["prepare_production", END])
    builder.add_edge("prepare_production", "production")
    builder.add_edge("production", END)

    return builder.compile(checkpointer=checkpointer)
