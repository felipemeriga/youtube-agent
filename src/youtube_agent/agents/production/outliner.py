from __future__ import annotations

import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from youtube_agent.state import ProductionState, VideoOutline

OUTLINER_PROMPT = """\
Você é um roteirista especialista em vídeos de YouTube para o canal "Além do Código", \
um canal brasileiro em português que cobre temas variados.

Tópico: {title}
Ângulo: {angle}

Pesquisa realizada:
{research}

Crie uma estrutura detalhada para o vídeo com:
1. sections: lista de seções, cada uma com "title", "description" e "duration" (em minutos)
2. hooks: 2-3 opções de ganchos provocativos para a abertura do vídeo
3. estimated_duration: duração total estimada do vídeo (ex: "14-16 min")

A estrutura deve incluir: abertura com gancho forte, seções principais com dados concretos, \
uma seção de análise/opinião, e fechamento com CTA.

Retorne APENAS um JSON object, sem outro texto.

JSON response:"""


def _generate_outline(state: ProductionState, llm: BaseChatModel) -> dict:
    research_text = "\n".join(
        f"[{f['tool']}] {f['content'][:500]}" for f in state["research_findings"][:10]
    )
    prompt = OUTLINER_PROMPT.format(
        title=state["topic"]["title"],
        angle=state["topic"]["angle"],
        research=research_text,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    outline = VideoOutline(
        sections=data.get("sections", []),
        hooks=data.get("hooks", []),
        estimated_duration=data.get("estimated_duration", "10-15 min"),
    )
    return {"outline": outline}


def _approve_outline(state: ProductionState) -> dict:
    decision = interrupt({"outline": state["outline"], "action": "Aprovar estrutura? [s/n/editar]"})
    if not decision.get("approved", False):
        return {"outline": None}
    return {}


def create_outliner_nodes(llm: BaseChatModel):
    def generate(state: ProductionState) -> dict:
        return _generate_outline(state, llm)

    return generate, _approve_outline
