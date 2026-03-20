from __future__ import annotations

import os
import uuid

import click
from langgraph.checkpoint.postgres import PostgresSaver
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


def _get_db_url() -> str:
    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        click.echo("Error: SUPABASE_DB_URL not set in .env", err=True)
        raise SystemExit(1)
    return db_url


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


def _stream_graph(graph, input_state, thread_config):
    for chunk in graph.stream(input_state, thread_config, stream_mode="updates", subgraphs=True):
        namespace, update = chunk
        node_name = list(update.keys())[0] if update else "unknown"
        display_status(f"▶ {node_name}")


def _run_interrupt_loop(graph, thread_config):
    state = graph.get_state(thread_config, subgraphs=True)
    while state.tasks:
        has_interrupts = False
        for task in state.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                has_interrupts = True
                for intr in task.interrupts:
                    resume_value = _handle_interrupt(intr.value)
                    _stream_graph(graph, Command(resume=resume_value), thread_config)
        if not has_interrupts:
            break
        state = graph.get_state(thread_config, subgraphs=True)


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
    db_url = _get_db_url()

    with PostgresSaver.from_conn_string(db_url) as checkpointer:
        checkpointer.setup()
        graph = create_orchestrator_graph(config, checkpointer=checkpointer)
        display_header("Ideação de Conteúdo", thread_id)
        thread_config = {"configurable": {"thread_id": thread_id}}
        _stream_graph(graph, {"mode": "ideate"}, thread_config)
        _run_interrupt_loop(graph, thread_config)


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

    db_url = _get_db_url()
    with PostgresSaver.from_conn_string(db_url) as checkpointer:
        checkpointer.setup()
        graph = create_orchestrator_graph(config, checkpointer=checkpointer)
        display_header("Produção de Vídeo", thread_id)
        thread_config = {"configurable": {"thread_id": thread_id}}
        _stream_graph(graph, input_state, thread_config)
        _run_interrupt_loop(graph, thread_config)


@cli.command()
@click.pass_context
def analyze(ctx):
    """Run channel analytics pipeline."""
    config = ctx.obj["config"]
    thread_id = str(uuid.uuid4())
    db_url = _get_db_url()

    with PostgresSaver.from_conn_string(db_url) as checkpointer:
        checkpointer.setup()
        graph = create_orchestrator_graph(config, checkpointer=checkpointer)
        display_header("Análise do Canal", thread_id)
        thread_config = {"configurable": {"thread_id": thread_id}}
        _stream_graph(graph, {"mode": "analyze"}, thread_config)
        _run_interrupt_loop(graph, thread_config)


@cli.command()
@click.pass_context
def full(ctx):
    """Run full pipeline: ideation then production."""
    config = ctx.obj["config"]
    thread_id = str(uuid.uuid4())
    db_url = _get_db_url()

    with PostgresSaver.from_conn_string(db_url) as checkpointer:
        checkpointer.setup()
        graph = create_orchestrator_graph(config, checkpointer=checkpointer)
        display_header("Pipeline Completo", thread_id)
        thread_config = {"configurable": {"thread_id": thread_id}}
        _stream_graph(graph, {"mode": "full"}, thread_config)
        _run_interrupt_loop(graph, thread_config)


@cli.command()
@click.option("--thread-id", required=True, help="Thread ID to resume")
@click.pass_context
def resume(ctx, thread_id):
    """Resume an interrupted session."""
    config = ctx.obj["config"]
    db_url = _get_db_url()

    with PostgresSaver.from_conn_string(db_url) as checkpointer:
        checkpointer.setup()
        graph = create_orchestrator_graph(config, checkpointer=checkpointer)
        display_header("Retomando Sessão", thread_id)
        thread_config = {"configurable": {"thread_id": thread_id}}
        state = graph.get_state(thread_config, subgraphs=True)
        if not state.tasks:
            console.print("[yellow]Nenhuma sessão pendente encontrada.[/yellow]")
            return
        _stream_graph(graph, None, thread_config)
        _run_interrupt_loop(graph, thread_config)


@cli.command()
@click.pass_context
def sessions(ctx):
    """List active/paused sessions."""
    from rich.table import Table

    db_url = _get_db_url()
    with PostgresSaver.from_conn_string(db_url) as checkpointer:
        checkpointer.setup()
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
