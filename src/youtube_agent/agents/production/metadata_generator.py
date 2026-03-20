from __future__ import annotations

import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command, interrupt

from youtube_agent.state import ProductionState, VideoMetadata

METADATA_PROMPT = """\
Você é um especialista em SEO para YouTube em português brasileiro.

Tópico do vídeo: {title}
Ângulo: {angle}
Resumo do roteiro: {script_preview}

Gere metadados otimizados para YouTube:
1. title_options: 3 opções de título (max 60 caracteres cada, em português)
2. description: descrição completa com keywords, timestamps e links úteis
3. tags: 15-20 tags relevantes em português
4. thumbnail_texts: 3 opções de texto curto para thumbnail (max 5 palavras)

Retorne APENAS um JSON object, sem outro texto.

JSON response:"""


def _generate_metadata(state: ProductionState, llm: BaseChatModel) -> dict:
    prompt = METADATA_PROMPT.format(
        title=state["topic"]["title"],
        angle=state["topic"]["angle"],
        script_preview=state["script"]["content"][:500],
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    metadata = VideoMetadata(
        title_options=data.get("title_options", []),
        description=data.get("description", ""),
        tags=data.get("tags", []),
        thumbnail_texts=data.get("thumbnail_texts", []),
    )
    return {"metadata": metadata}


def _approve_metadata(state: ProductionState) -> Command[Literal["__end__"]]:
    decision = interrupt({"metadata": state["metadata"], "action": "Aprovar metadados? [s/n]"})
    if not decision.get("approved", False):
        return Command(update={"metadata": None}, goto="__end__")
    return Command(goto="__end__")


def create_metadata_nodes(llm: BaseChatModel):
    def generate(state: ProductionState) -> dict:
        return _generate_metadata(state, llm)

    return generate, _approve_metadata
