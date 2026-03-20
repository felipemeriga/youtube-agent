from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from youtube_agent.state import ProductionState, VideoScript

WRITER_PROMPT = """\
Você é um roteirista profissional de vídeos de YouTube para o canal "Além do Código", \
um canal brasileiro em português.

Tópico: {title}
Ângulo: {angle}

Estrutura aprovada:
{outline}

Pesquisa realizada (com fontes):
{research}

Escreva o roteiro completo seguindo EXATAMENTE este formato em Markdown:

---

# [Título do Vídeo]

## ⏱️ TIMING ([duração estimada])

| Seção | Tempo | Duração |
| --- | --- | --- |
| [Seção 1] | 0:00 - X:XX | X:XX |
| [Seção 2] | X:XX - X:XX | X:XX |
(uma linha para cada seção da estrutura aprovada)

---

## 📊 STATS E DADOS (com fontes pra citar)

(Para cada dado relevante da pesquisa, use este formato:)

> **Dado N**: [Estatística ou fato concreto encontrado na pesquisa]
>
> *Fonte: [Nome da fonte]*

(Inclua 5-10 dados com suas fontes. Use APENAS dados reais da pesquisa fornecida.)

---

## 🎙️ TALKING POINTS (frases prontas pra falar)

(5-8 frases curtas, provocativas, no tom conversacional do canal. Cada uma em um bullet.)

- "frase 1"
- "frase 2"

---

## 📝 ROTEIRO COMPLETO

### 🎬 ABERTURA (0:00 - X:XX)

"[Falas naturais e conversacionais]"

### 📌 [SEÇÃO 1] (X:XX - X:XX)

"[Falas com dados, exemplos, transições]"

(Repetir para cada seção da estrutura)

### 🎬 FECHAMENTO (X:XX - X:XX)

"[Fechamento + CTA para inscrição e comentários]"

---

## 🔗 FONTES VERIFICADAS

1. **[Nome da fonte]** — [Descrição curta] — [URL se disponível]
2. **[Nome da fonte]** — [Descrição curta] — [URL se disponível]

---

REGRAS IMPORTANTES:
- Todas as falas em português brasileiro, tom conversacional
- APENAS use dados e fontes que vieram da pesquisa fornecida acima
- NÃO invente dados, estatísticas ou fontes
- Inclua URLs reais das fontes quando disponíveis na pesquisa
- Notas para o apresentador entre [colchetes]
- Os talking points devem ser frases prontas, provocativas, que funcionam como sound bites
- O timing deve ser realista e somar a duração total estimada

Escreva o roteiro completo:"""


def _write_script(state: ProductionState, llm: BaseChatModel) -> dict:
    outline_text = "\n".join(
        f"{i + 1}. {s.get('title', '')} ({s.get('duration', '')}): {s.get('description', '')}"
        for i, s in enumerate(state["outline"]["sections"])
    )
    research_text = "\n".join(
        f"- [{f.get('tool', 'web')}] {f['content'][:500]}\n  Fonte: {f.get('source', 'N/A')}"
        for f in state["research_findings"][:15]
    )
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


def _approve_script(state: ProductionState) -> dict:
    decision = interrupt(
        {
            "script_preview": state["script"]["content"][:500] + "...",
            "word_count": state["script"]["word_count"],
            "action": "Aprovar roteiro? [s/n]",
        }
    )
    if not decision.get("approved", False):
        return {"script": None}
    return {}


def create_writer_nodes(llm: BaseChatModel):
    def write(state: ProductionState) -> dict:
        return _write_script(state, llm)

    return write, _approve_script
