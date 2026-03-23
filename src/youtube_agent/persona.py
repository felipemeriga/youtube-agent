from __future__ import annotations


def format_persona(persona: dict) -> str:
    if not persona:
        return ""

    host = persona.get("host", {})
    style = host.get("style", {})
    opinions = host.get("opinions", {})
    avoid = host.get("avoid", [])

    parts = []

    if host.get("background"):
        parts.append(f"Sobre o apresentador: {host['background'].strip()}")

    if style:
        style_lines = [f"- {k}: {v}" for k, v in style.items()]
        parts.append("Estilo de comunicação:\n" + "\n".join(style_lines))

    if opinions:
        opinion_lines = []
        for category, items in opinions.items():
            for item in items:
                opinion_lines.append(f"- {item}")
        parts.append("Opiniões e posicionamentos:\n" + "\n".join(opinion_lines))

    if avoid:
        avoid_lines = [f"- {item}" for item in avoid]
        parts.append("O que EVITAR:\n" + "\n".join(avoid_lines))

    if not parts:
        return ""

    return "PERSONA DO CANAL:\n\n" + "\n\n".join(parts)
