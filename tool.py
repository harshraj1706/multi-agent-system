import os
import re

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_core.tools import tool
from readability import Document
from tavily import TavilyClient

load_dotenv()

MAX_SCRAPED_CHARS = int(os.getenv("MAX_SCRAPED_CHARS", "5000"))


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. Add it to your .env file before running the pipeline."
        )
    return value


tavily_client = TavilyClient(api_key=_require_env("TAVILY_API_KEY"))


def extract_main_content(url: str) -> str:
    """
    Extract clean article content from a URL.

    Readability works best with server-rendered HTML. JavaScript-heavy pages may
    return very little useful text.
    """
    if not url:
        return "Could not scrape page: missing URL."

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), "html.parser")

        for tag in soup(
            ["script", "style", "iframe", "img", "svg", "video", "audio", "form"]
        ):
            tag.decompose()

        text = soup.get_text("\n", strip=True)
        text = re.sub(r"\n\s*\n+", "\n\n", text)

        if not text:
            return "Could not scrape page: no readable article text found."
        return text[:MAX_SCRAPED_CHARS]

    except requests.RequestException as exc:
        return f"Could not scrape page: request failed ({exc})."
    except Exception as exc:
        return f"Could not scrape page: {exc}."


@tool
def web_search(query: str) -> str:
    """
    Search the web using Tavily, then scrape the top results.

    Returns compact title, URL, snippet, and extracted page content.
    """
    if not query:
        return "Search query is empty."

    try:
        search_results = tavily_client.search(
            query=query,
            max_results=int(os.getenv("TAVILY_MAX_RESULTS", "3")),
        )
    except Exception as exc:
        return f"Search failed: {exc}"

    results = search_results.get("results", [])
    if not results:
        return "No search results found."

    final_output = []
    for idx, result in enumerate(results, start=1):
        title = result.get("title") or "N/A"
        url = result.get("url") or ""
        snippet = result.get("content") or "N/A"
        scraped_content = extract_main_content(url)

        final_output.append(
            f"RESULT {idx}\n"
            f"TITLE: {title}\n"
            f"URL: {url}\n"
            f"SNIPPET: {snippet}\n"
            f"CONTENT:\n{scraped_content}"
        )

    return "\n".join(final_output)


@tool
def scrape_url(url: str) -> str:
    """Scrape and extract the main article content from a specific URL."""
    return extract_main_content(url)
