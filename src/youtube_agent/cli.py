from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager

import click
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from rich.console import Console

from youtube_agent.config import load_config
from youtube_agent.display import (
    display_header,
    display_outline,
    display_status,
    display_topics,
    prompt_approval,
)
from youtube_agent.graph import create_orchestrator_graph

console = Console()


@contextmanager
def _get_checkpointer(config):
    if config.persistence.backend == "postgres":
        from langgraph.checkpoint.postgres import PostgresSaver

        with PostgresSaver.from_conn_string(config.persistence.postgres_url) as cp:
            yield cp
    else:
        conn = sqlite3.connect(config.persistence.sqlite_path, check_same_thread=False)
        cp = SqliteSaver(conn)
        try:
            yield cp
        finally:
            conn.close()


def _handle_interrupt(interrupt_data: dict) -> dict:
    action = interrupt_data.get("action", "")

    if "suggested_topics" in interrupt_data:
        display_topics(interrupt_data["suggested_topics"])
        choice = prompt_approval(action)
        try:
            index = int(choice)
        except ValueError:
            index = 0
        return {"selected_index": index}

    if "outline" in interrupt_data:
        display_outline(interrupt_data["outline"])
        choice = prompt_approval(action)
        return {"approved": choice.lower() in ("s", "sim", "y", "yes")}

    if "script_preview" in interrupt_data:
        console.print(f"\n[dim]{interrupt_data['script_preview']}[/dim]")
        console.print(f"[cyan]Palavras: {interrupt_data.get('word_count', '?')}[/cyan]")
        choice = prompt_approval(action)
        return {"approved": choice.lower() in ("s", "sim", "y", "yes")}

    if "metadata" in interrupt_data:
        metadata = interrupt_data["metadata"]
        console.print("\n[bold]Títulos:[/bold]")
        for i, t in enumerate(metadata.get("title_options", []), 1):
            console.print(f"  {i}. {t}")
        console.print(f"\n[bold]Tags:[/bold] {', '.join(metadata.get('tags', []))}")
        console.print(f"\n[bold]Thumbnail:[/bold] {metadata.get('thumbnail_texts', [])}")
        choice = prompt_approval(action)
        return {"approved": choice.lower() in ("s", "sim", "y", "yes")}

    if "strategy" in interrupt_data:
        strategy = interrupt_data["strategy"]
        for key, value in strategy.items():
            console.print(f"\n[bold]{key}:[/bold] {value}")
        prompt_approval(action)
        return {}

    choice = prompt_approval(action)
    return {"approved": choice.lower() in ("s", "sim", "y", "yes")}


def _run_graph(graph, input_state: dict, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 50}

    for chunk in graph.stream(input_state, config, stream_mode="updates", subgraphs=True):
        namespace, update = chunk
        node_name = list(update.keys())[0] if update else "unknown"
        display_status(f"▶ {node_name}")

    while True:
        state = graph.get_state(config, subgraphs=True)
        if not state.tasks:
            break
        has_interrupts = False
        for task in state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                has_interrupts = True
                for intr in task.interrupts:
                    resume_value = _handle_interrupt(intr.value)
                    for chunk in graph.stream(
                        Command(resume=resume_value),
                        config,
                        stream_mode="updates",
                        subgraphs=True,
                    ):
                        namespace, update = chunk
                        node_name = list(update.keys())[0] if update else "unknown"
                        display_status(f"▶ {node_name}")
        if not has_interrupts:
            break


def _handle_resume(graph, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    while True:
        state = graph.get_state(config, subgraphs=True)
        if not state.tasks:
            break
        has_interrupts = False
        for task in state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                has_interrupts = True
                for intr in task.interrupts:
                    resume_value = _handle_interrupt(intr.value)
                    for chunk in graph.stream(
                        Command(resume=resume_value),
                        config,
                        stream_mode="updates",
                        subgraphs=True,
                    ):
                        namespace, update = chunk
                        node_name = list(update.keys())[0] if update else "unknown"
                        display_status(f"▶ {node_name}")
        if not has_interrupts:
            break


@click.group()
@click.option("--config", "config_path", default=None, help="Path to config.yaml")
@click.pass_context
def cli(ctx, config_path):
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config_path)


@cli.command()
@click.pass_context
def ideate(ctx):
    """Run content ideation pipeline."""
    config = ctx.obj["config"]
    thread_id = str(uuid.uuid4())
    with _get_checkpointer(config) as checkpointer:
        graph = create_orchestrator_graph(config, checkpointer=checkpointer)
        display_header("Ideação de Conteúdo", thread_id)
        _run_graph(graph, {"mode": "ideate"}, thread_id)


@cli.command()
@click.option("--topic", default=None, help="Topic title for the video")
@click.pass_context
def produce(ctx, topic):
    """Run video production pipeline."""
    config = ctx.obj["config"]
    thread_id = str(uuid.uuid4())

    if topic:
        input_state = {
            "mode": "produce",
            "selected_topic": {
                "title": topic,
                "angle": "",
                "timeliness": "",
                "estimated_interest": "high",
            },
            "topic": {
                "title": topic,
                "angle": "",
                "timeliness": "",
                "estimated_interest": "high",
            },
        }
    else:
        topic_input = console.input("[bold yellow]? Qual o tópico do vídeo?[/bold yellow] ")
        input_state = {
            "mode": "produce",
            "selected_topic": {
                "title": topic_input,
                "angle": "",
                "timeliness": "",
                "estimated_interest": "high",
            },
            "topic": {
                "title": topic_input,
                "angle": "",
                "timeliness": "",
                "estimated_interest": "high",
            },
        }

    with _get_checkpointer(config) as checkpointer:
        graph = create_orchestrator_graph(config, checkpointer=checkpointer)
        display_header("Produção de Vídeo", thread_id)
        _run_graph(graph, input_state, thread_id)


@cli.command()
@click.pass_context
def analyze(ctx):
    """Run channel analytics pipeline."""
    config = ctx.obj["config"]
    thread_id = str(uuid.uuid4())
    with _get_checkpointer(config) as checkpointer:
        graph = create_orchestrator_graph(config, checkpointer=checkpointer)
        display_header("Análise do Canal", thread_id)
        _run_graph(graph, {"mode": "analyze"}, thread_id)


@cli.command()
@click.pass_context
def full(ctx):
    """Run full pipeline: ideation then production."""
    config = ctx.obj["config"]
    thread_id = str(uuid.uuid4())
    with _get_checkpointer(config) as checkpointer:
        graph = create_orchestrator_graph(config, checkpointer=checkpointer)
        display_header("Pipeline Completo", thread_id)
        _run_graph(graph, {"mode": "full"}, thread_id)


@cli.command()
@click.argument("thread_id")
@click.pass_context
def resume(ctx, thread_id):
    """Resume an interrupted session."""
    config = ctx.obj["config"]
    with _get_checkpointer(config) as checkpointer:
        graph = create_orchestrator_graph(config, checkpointer=checkpointer)
        display_header("Retomando Sessão", thread_id)
        graph_config = {"configurable": {"thread_id": thread_id}}
        state = graph.get_state(graph_config, subgraphs=True)
        if not state.tasks:
            console.print("[yellow]Nenhuma sessão pendente encontrada.[/yellow]")
            return
        _handle_resume(graph, thread_id)


@cli.command()
@click.pass_context
def sessions(ctx):
    """List active/paused sessions."""
    config = ctx.obj["config"]
    from rich.table import Table

    with _get_checkpointer(config) as checkpointer:
        table = Table(title="Sessões", border_style="blue")
        table.add_column("Thread ID", style="cyan")
        table.add_column("Status")
        table.add_column("Checkpoint")
        for checkpoint_tuple in checkpointer.list(None):
            tid = checkpoint_tuple.config.get("configurable", {}).get("thread_id", "?")
            ts = checkpoint_tuple.checkpoint.get("ts", "?")
            table.add_row(tid, "paused", ts)
        console.print(table)


if __name__ == "__main__":
    cli()
