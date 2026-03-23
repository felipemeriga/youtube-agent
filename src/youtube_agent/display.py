from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

_console = Console()


def get_console() -> Console:
    return _console


def display_header(title: str, thread_id: str, console: Console | None = None) -> None:
    c = console or _console
    c.print(Panel(f"{title}\nThread: {thread_id}", title="YouTube Agent", border_style="blue"))


def display_topics(topics: list[dict], console: Console | None = None) -> None:
    c = console or _console
    table = Table(title="Sugestões de Tópicos", border_style="green")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Título", style="bold")
    table.add_column("Ângulo")
    table.add_column("Interesse", style="magenta")
    for i, topic in enumerate(topics, 1):
        table.add_row(
            str(i),
            topic.get("title", ""),
            topic.get("angle", ""),
            topic.get("estimated_interest", ""),
        )
    c.print(table)


def display_outline(outline: dict, console: Console | None = None) -> None:
    c = console or _console
    sections = outline.get("sections", [])
    lines = [
        f"  {i + 1}. {s.get('title', '')} — {s.get('description', '')}"
        for i, s in enumerate(sections)
    ]
    c.print(Panel("\n".join(lines), title="Roteiro — Estrutura", border_style="green"))


def display_status(status: str, console: Console | None = None) -> None:
    c = console or _console
    c.print(f"\n[bold cyan]{status}[/bold cyan]")


def display_saved(path: str, console: Console | None = None) -> None:
    c = console or _console
    c.print(f"\n[bold green]Salvo em {path}[/bold green]")


def prompt_approval(message: str, console: Console | None = None) -> str:
    c = console or _console
    return c.input(f"\n[bold yellow]? {message}[/bold yellow] ")
