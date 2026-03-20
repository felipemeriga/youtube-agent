from __future__ import annotations

from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command, interrupt

from youtube_agent.state import ProductionState, VideoScript

WRITER_PROMPT = """\
Você é um roteirista de vídeos de YouTube. Escreva um roteiro completo em português \
para o canal "Além do Código", voltado para desenvolvedores brasileiros.

Tópico: {title}
Ângulo: {angle}

Estrutura aprovada:
{outline}

Pesquisa:
{research}

Escreva o roteiro completo incluindo:
- Falas naturais e conversacionais (como se estivesse conversando com o espectador)
- Notas para o apresentador entre [colchetes]
- Indicações de transição entre seções
- Marcações de tempo aproximadas
- CTA para inscrição e comentários

Escreva o roteiro completo abaixo:"""


def _write_script(state: ProductionState, llm: BaseChatModel) -> dict:
    outline_text = "\n".join(
        f"{i + 1}. {s.get('title', '')} ({s.get('duration', '')}): {s.get('description', '')}"
        for i, s in enumerate(state["outline"]["sections"])
    )
    research_text = "\n".join(f"- {f['content'][:300]}" for f in state["research_findings"][:8])
    prompt = WRITER_PROMPT.format(
        title=state["topic"]["title"],
        angle=state["topic"]["angle"],
        outline=outline_text,
        research=research_text,
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    script = VideoScript(content=content, word_count=len(content.split()))
    return {"script": script}


def _approve_script(state: ProductionState) -> Command[Literal["__end__"]]:
    decision = interrupt(
        {
            "script_preview": state["script"]["content"][:500] + "...",
            "word_count": state["script"]["word_count"],
            "action": "Aprovar roteiro? [s/n]",
        }
    )
    if not decision.get("approved", False):
        return Command(update={"script": None}, goto="__end__")
    return Command(goto="__end__")


def create_writer_nodes(llm: BaseChatModel):
    def write(state: ProductionState) -> dict:
        return _write_script(state, llm)

    return write, _approve_script
