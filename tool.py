"""
Tool adapter definitions for search and web scraping.
Maintains full backward compatibility with legacy imports while utilizing the upgraded cognisynth modules.
"""

import sys
from pathlib import Path

# Ensure src/ is on python path
src_path = str(Path(__file__).resolve().parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from langchain_core.tools import tool
from cognisynth.tools.scraper import extract_main_content as _extract_main_content
from cognisynth.tools.search import search_web_structured, format_search_summary_for_llm


def extract_main_content(url: str) -> str:
    """Extract clean article content from a URL (returns string for backward compatibility)."""
    doc = _extract_main_content(url)
    return doc.text


@tool
def web_search(query: str) -> str:
    """
    Search the web using Tavily, then scrape the top results.
    Returns compact title, URL, snippet, and extracted page content.
    """
    sources, documents = search_web_structured(query, max_results=3, scrape_pages=True)
    if not sources:
        return "No search results found."
    return format_search_summary_for_llm(sources, documents)


@tool
def scrape_url(url: str) -> str:
    """Scrape and extract the main article content from a specific URL."""
    return extract_main_content(url)
