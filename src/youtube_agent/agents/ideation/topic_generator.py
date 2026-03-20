from __future__ import annotations

import json
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command, interrupt

from youtube_agent.state import IdeationState, TopicSuggestion

TOPIC_PROMPT = """\
Você é um especialista em estratégia de conteúdo para YouTube.

O canal "Além do Código" é um canal brasileiro em português que aborda temas variados como \
tecnologia, desenvolvimento de software, carreira internacional, soft-skills, geopolítica, \
economia e outros assuntos relevantes para profissionais de tecnologia e público geral.

Abaixo estão dados reais coletados de diversas fontes. Use APENAS estes dados como base \
para suas sugestões. Não invente tendências ou dados que não estejam listados abaixo.

Dados de tendências coletados:
{trends}

Estatísticas do canal:
{channel_stats}

Vídeos de melhor performance dos concorrentes:
{competitor_insights}

{hints_section}

Com base EXCLUSIVAMENTE nos dados acima, sugira 5-10 tópicos para novos vídeos. \
Para cada tópico, forneça:
1. title: título do vídeo (em português)
2. angle: ângulo/abordagem específica
3. timeliness: por que este tópico é relevante agora (cite a fonte/tendência que motivou)
4. estimated_interest: "high", "medium" ou "low"

Regras:
- Cada sugestão DEVE ser baseada em pelo menos uma tendência ou dado real listado acima
- NÃO invente tendências ou informações
- Os títulos devem ser em português
- Considere o que está performando bem nos concorrentes para identificar oportunidades

Retorne APENAS um JSON array de objetos, sem outro texto.

JSON response:"""


def _generate_topics(state: IdeationState, llm: BaseChatModel) -> dict:
    trends_text = "\n".join(
        f"- [{t['source']}] {t['title']} (score: {t['score']})" for t in state["trends"][:30]
    )
    channel_text = str(state.get("channel_stats") or "Sem dados do canal")
    competitor_text = "\n".join(
        f"- {c['channel_name']}: {c['title']} ({c['views']} views)"
        for c in state.get("competitor_insights", [])[:15]
    )

    user_prompt = state.get("prompt") or ""
    if user_prompt:
        hints_section = (
            "O criador do canal pediu especificamente:\n"
            f'"{user_prompt}"\n\n'
            "Priorize sugestões de tópicos alinhadas com este pedido, "
            "mas sempre baseadas nos dados reais coletados acima."
        )
    else:
        hints_section = ""

    prompt = TOPIC_PROMPT.format(
        trends=trends_text,
        channel_stats=channel_text,
        competitor_insights=competitor_text or "Sem dados de concorrentes",
        hints_section=hints_section,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    topics = json.loads(raw)
    suggestions = [
        TopicSuggestion(
            title=t["title"],
            angle=t["angle"],
            timeliness=t["timeliness"],
            estimated_interest=t["estimated_interest"],
        )
        for t in topics
    ]
    return {"suggested_topics": suggestions}


def _approve_topic(state: IdeationState) -> Command[Literal["__end__"]]:
    decision = interrupt(
        {
            "suggested_topics": state["suggested_topics"],
            "action": "Escolha um tópico pelo número (ou 0 para cancelar):",
        }
    )
    index = decision.get("selected_index", 0)
    if index <= 0 or index > len(state["suggested_topics"]):
        return Command(update={"selected_topic": None}, goto="__end__")
    selected = state["suggested_topics"][index - 1]
    return Command(update={"selected_topic": selected}, goto="__end__")


def create_topic_generator_nodes(llm: BaseChatModel):
    def generate(state: IdeationState) -> dict:
        return _generate_topics(state, llm)

    return generate, _approve_topic
