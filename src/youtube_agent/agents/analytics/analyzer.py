from __future__ import annotations

import json

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from youtube_agent.state import AnalysisReport, AnalyticsState

ANALYZER_PROMPT = """\
Você é um analista de dados especializado em YouTube. Analise os seguintes dados \
do canal "Além do Código" e do mercado.

{topic_section}

Vídeos do canal:
{channel_videos}

Vídeos de concorrentes:
{competitor_videos}

{topic_videos_section}

Forneça uma análise com:
1. top_performing: IDs e títulos dos 5 vídeos com melhor desempenho (do canal ou do mercado)
2. bottom_performing: IDs e títulos dos 5 vídeos com pior desempenho do canal
3. patterns: padrões identificados (temas, títulos, formatos que performam bem)
4. competitor_comparison: como o canal se compara ao que está performando no mercado

{topic_analysis_instruction}

Retorne APENAS um JSON object com essas 4 chaves. \
Para top_performing e bottom_performing, use arrays de objects com \
video_id, title, views, likes, comments, published_at, channel_id.

JSON response:"""


def _analyze(state: AnalyticsState, llm: BaseChatModel) -> dict:
    topic_context = state.get("topic_context") or ""

    channel_text = "\n".join(
        f"- {v['title']} | views: {v['views']} | likes: {v['likes']}"
        f" | comments: {v['comments']} | {v['published_at']}"
        for v in state["channel_videos"]
    )
    competitor_text = "\n".join(
        f"- {v['title']} | views: {v['views']} | likes: {v['likes']} | {v['published_at']}"
        for v in state.get("competitor_videos", [])[:20]
    )

    if topic_context:
        topic_section = f'Tema em análise: "{topic_context}"'
        topic_videos = state.get("topic_videos", [])
        if topic_videos:
            topic_videos_text = "\n".join(
                f"- {v['title']} | views: {v['views']} | likes: {v['likes']}"
                f" | comments: {v['comments']} | {v['published_at']}"
                for v in topic_videos
            )
            topic_videos_section = (
                f"Vídeos sobre este tema no YouTube (últimos 30 dias):\n{topic_videos_text}"
            )
        else:
            topic_videos_section = "Sem vídeos encontrados sobre este tema."
        topic_analysis_instruction = (
            "IMPORTANTE: Foque a análise em como este tema específico está performando no YouTube. "
            "Quais abordagens funcionam? Quais títulos atraem mais views? "
            "Como o canal pode se posicionar melhor que os vídeos existentes sobre o tema?"
        )
    else:
        topic_section = ""
        topic_videos_section = ""
        topic_analysis_instruction = ""

    prompt = ANALYZER_PROMPT.format(
        topic_section=topic_section,
        channel_videos=channel_text or "Sem dados",
        competitor_videos=competitor_text or "Sem dados de concorrentes",
        topic_videos_section=topic_videos_section,
        topic_analysis_instruction=topic_analysis_instruction,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw)
    report = AnalysisReport(
        top_performing=data.get("top_performing", []),
        bottom_performing=data.get("bottom_performing", []),
        patterns=data.get("patterns", ""),
        competitor_comparison=data.get("competitor_comparison", ""),
    )
    return {"analysis": report}


def create_analyzer_node(llm: BaseChatModel):
    def analyze(state: AnalyticsState) -> dict:
        return _analyze(state, llm)

    return analyze
