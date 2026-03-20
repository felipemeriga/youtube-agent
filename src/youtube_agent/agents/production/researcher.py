from __future__ import annotations

import asyncio
import logging

from youtube_agent.state import ProductionState
from youtube_agent.tools.scraper import scrape_page
from youtube_agent.tools.tavily_search import search_web

logger = logging.getLogger(__name__)


async def _research_async(state: ProductionState) -> dict:
    topic = state["topic"]
    queries = [
        topic["title"],
        f"{topic['title']} {topic['angle']}",
        f"{topic['title']} tutorial guia",
    ]

    all_findings = []
    for query in queries:
        try:
            results = search_web(query)
            all_findings.extend(results)
            urls_to_scrape = [r["source"] for r in results[:2] if r["source"].startswith("http")]
            for url in urls_to_scrape:
                try:
                    content = await scrape_page(url)
                    if not content.startswith("Error"):
                        all_findings.append(
                            {
                                "query": query,
                                "source": url,
                                "content": content[:3000],
                                "tool": "playwright",
                            }
                        )
                except Exception as e:
                    logger.warning("Scrape failed for '%s': %s", url, e)
        except Exception as e:
            logger.warning("Search failed for '%s': %s", query, e)

    return {"research_findings": all_findings}


def research_topic(state: ProductionState) -> dict:
    return asyncio.run(_research_async(state))
