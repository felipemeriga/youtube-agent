from __future__ import annotations

from langchain_tavily import TavilySearch

from youtube_agent.state import ResearchFinding

_tavily_tool: TavilySearch | None = None


def create_tavily_tool(max_results: int = 5) -> TavilySearch:
    global _tavily_tool
    _tavily_tool = TavilySearch(max_results=max_results)
    return _tavily_tool


def _parse_results(query: str, raw: object) -> list[ResearchFinding]:
    if isinstance(raw, str):
        return [ResearchFinding(query=query, source="tavily", content=raw, tool="tavily")]
    results = raw.get("results", []) if isinstance(raw, dict) else raw
    findings: list[ResearchFinding] = []
    for r in results:
        findings.append(
            ResearchFinding(
                query=query,
                source=r.get("url", "unknown"),
                content=r.get("content", ""),
                tool="tavily",
            )
        )
    return findings


def search_web(query: str, max_results: int = 5) -> list[ResearchFinding]:
    if _tavily_tool is None:
        raise RuntimeError("Tavily tool not initialized. Call create_tavily_tool() first.")
    raw = _tavily_tool.invoke(query)
    return _parse_results(query, raw)[:max_results]
