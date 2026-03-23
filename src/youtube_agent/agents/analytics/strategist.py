from __future__ import annotations

import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from youtube_agent.state import AnalyticsState, StrategyReport

STRATEGIST_PROMPT = """\
Você é um estrategista de conteúdo para YouTube para o canal "Além do Código", \
um canal brasileiro em português.

{topic_section}

Análise do canal:
Padrões: {patterns}
Comparação com mercado: {competitor_comparison}

Com base nessa análise, crie uma estratégia com:
1. content_suggestions: sugestões de conteúdo específicas para este tema/canal
2. title_patterns: padrões de título que funcionam melhor (baseado nos dados reais)
3. posting_recommendations: frequência e timing ideal
4. growth_opportunities: oportunidades baseadas nas lacunas encontradas no mercado

{topic_strategy_instruction}

Escreva tudo em português, de forma prática e acionável. \
Base suas recomendações nos DADOS REAIS da análise, não em conselhos genéricos.

Retorne APENAS um JSON object com essas 4 chaves, valores como strings detalhadas.

JSON response:"""


def _generate_strategy(state: AnalyticsState, llm: BaseChatModel) -> dict:
    analysis = state.get("analysis")
    topic_context = state.get("topic_context") or ""

    if topic_context:
        topic_section = f'Tema em análise: "{topic_context}"'
        topic_strategy_instruction = (
            "IMPORTANTE: Todas as recomendações devem ser específicas para este tema. "
            "Não dê conselhos genéricos de canal. Diga exatamente como abordar ESTE tema "
            "para maximizar views e engajamento, baseado no que está funcionando no mercado."
        )
    else:
        topic_section = ""
        topic_strategy_instruction = ""

    prompt = STRATEGIST_PROMPT.format(
        topic_section=topic_section,
        patterns=analysis["patterns"] if analysis else "Sem dados",
        competitor_comparison=analysis["competitor_comparison"] if analysis else "Sem dados",
        topic_strategy_instruction=topic_strategy_instruction,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    strategy = StrategyReport(
        content_suggestions=data.get("content_suggestions", ""),
        title_patterns=data.get("title_patterns", ""),
        posting_recommendations=data.get("posting_recommendations", ""),
        growth_opportunities=data.get("growth_opportunities", ""),
    )
    return {"strategy": strategy}


def _approve_strategy(state: AnalyticsState) -> dict:
    decision = interrupt({"strategy": state["strategy"], "action": "Aprovar estratégia? [s/n]"})
    if not decision.get("approved", False):
        return {"strategy": None}
    return {}


def create_strategist_nodes(llm: BaseChatModel):
    def generate(state: AnalyticsState) -> dict:
        return _generate_strategy(state, llm)

    return generate, _approve_strategy
