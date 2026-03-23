from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from youtube_agent.agents.production.metadata_generator import create_metadata_nodes
from youtube_agent.agents.production.outliner import create_outliner_nodes
from youtube_agent.agents.production.researcher import research_topic
from youtube_agent.agents.production.writer import create_writer_nodes
from youtube_agent.state import ProductionState
from youtube_agent.tools.tavily_search import create_tavily_tool
from youtube_agent.utils import get_output_dir, save_json, save_text


def create_production_graph(
    outliner_llm: BaseChatModel,
    writer_llm: BaseChatModel,
    metadata_llm: BaseChatModel,
    output_dir: str = "./output",
) -> StateGraph:
    create_tavily_tool(max_results=5)
    generate_outline, approve_outline = create_outliner_nodes(outliner_llm)
    write_script, approve_script = create_writer_nodes(writer_llm)
    generate_metadata, approve_metadata = create_metadata_nodes(metadata_llm)

    builder = StateGraph(ProductionState)
    builder.add_node("researcher", research_topic)
    builder.add_node("outliner", generate_outline)
    builder.add_node("approve_outline", approve_outline)
    builder.add_node("writer", write_script)
    builder.add_node("approve_script", approve_script)
    builder.add_node("metadata_generator", generate_metadata)
    builder.add_node("approve_metadata", approve_metadata)

    builder.add_edge(START, "researcher")
    builder.add_edge("researcher", "outliner")
    builder.add_edge("outliner", "approve_outline")

    def _route_after_outline(state: ProductionState):
        if state.get("outline") is None:
            return END
        return "writer"

    def _route_after_script(state: ProductionState):
        if state.get("script") is None:
            return END
        return "metadata_generator"

    def _route_after_metadata(state: ProductionState):
        if state.get("metadata") is None:
            return END
        return "save_output"

    builder.add_conditional_edges("approve_outline", _route_after_outline, ["writer", END])
    builder.add_conditional_edges(
        "approve_script", _route_after_script, ["metadata_generator", END]
    )

    builder.add_edge("writer", "approve_script")
    builder.add_edge("metadata_generator", "approve_metadata")

    def _save_output(state: ProductionState) -> dict:
        out = get_output_dir(output_dir, state["topic"]["title"])
        if state.get("script"):
            save_text(out / "script.md", state["script"]["content"])
        if state.get("outline"):
            save_json(out / "outline.json", state["outline"])
        if state.get("metadata"):
            save_json(out / "metadata.json", state["metadata"])
        return {}

    builder.add_node("save_output", _save_output)
    builder.add_conditional_edges("approve_metadata", _route_after_metadata, ["save_output", END])
    builder.add_edge("save_output", END)

    return builder
