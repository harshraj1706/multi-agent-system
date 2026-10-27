"""
Tavily Search adapter producing structured Source and Document records.
"""

from urllib.parse import urlparse
from typing import Optional
from tavily import TavilyClient

from cognisynth.config import settings
from cognisynth.logging_config import logger
from cognisynth.schemas.evidence import Source, SourceType, Document
from cognisynth.tools.scraper import extract_main_content


def _infer_source_type(domain: str) -> SourceType:
    """Classify domain into high-level source type."""
    domain_lower = domain.lower()
    if any(domain_lower.endswith(tld) for tld in [".edu", ".ac.uk"]):
        return SourceType.ACADEMIC
    if any(domain_lower.endswith(tld) for tld in [".gov", ".mil"]):
        return SourceType.GOVERNMENT
    if any(keyword in domain_lower for keyword in ["reuters", "bloomberg", "bbc", "nytimes", "wsj", "theverge"]):
        return SourceType.NEWS
    if any(keyword in domain_lower for keyword in ["docs.", "developer.", "github.com", "arxiv.org", "nature.com"]):
        return SourceType.TECHNICAL_DOCS
    if any(keyword in domain_lower for keyword in ["medium.com", "substack.com", "blog"]):
        return SourceType.BLOG
    return SourceType.GENERAL_WEB


def search_web_structured(
    query: str,
    max_results: Optional[int] = None,
    scrape_pages: bool = True,
) -> tuple[list[Source], list[Document]]:
    """
    Search the web with Tavily and return typed (Source, Document) pairs.
    """
    if not query or not query.strip():
        return [], []

    api_key = settings.tavily_api_key
    if not api_key:
        logger.error("Tavily API key not found in configuration.")
        return [], []

    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query.strip(),
            max_results=max_results or settings.tavily_max_results,
        )
    except Exception as exc:
        logger.error(f"Tavily search API failed for query '{query}': {exc}")
        return [], []

    raw_results = response.get("results", [])
    sources: list[Source] = []
    documents: list[Document] = []

    disallowed_domains = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com", "facebook.com", "twitter.com", "x.com", "pinterest.com", "vimeo.com"]

    for item in raw_results:
        url = item.get("url") or ""
        title = item.get("title") or "Untitled Web Source"
        snippet = item.get("content") or ""

        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # Skip video/social media pages that lack article text
        if any(d in domain for d in disallowed_domains):
            continue

        source = Source(
            url=url,
            title=title,
            domain=domain,
            publisher=domain,
            source_type=_infer_source_type(domain),
            metadata={"snippet": snippet},
        )
        sources.append(source)

        if scrape_pages and url:
            doc = extract_main_content(url, source_id=source.source_id)
            # If scraping returns empty/failed text, fallback to snippet
            if len(doc.text) < 100 and snippet:
                doc.text = f"{snippet}\n\n[Full-page scrape yielded minimal text; used search snippet.]"
            documents.append(doc)
        else:
            documents.append(
                Document(
                    source_id=source.source_id,
                    text=snippet,
                    extraction_method="tavily_snippet",
                )
            )

    return sources, documents


def format_search_summary_for_llm(sources: list[Source], documents: list[Document]) -> str:
    """Format structured sources and documents into structured text for LLMs."""
    doc_map = {doc.source_id: doc.text for doc in documents}
    parts = []
    for idx, src in enumerate(sources, start=1):
        doc_text = doc_map.get(src.source_id, src.metadata.get("snippet", ""))
        parts.append(
            f"--- SOURCE #{idx} ---\n"
            f"SOURCE_ID: {src.source_id}\n"
            f"TITLE: {src.title}\n"
            f"URL: {src.url}\n"
            f"DOMAIN: {src.domain} (Type: {src.source_type.value}, Quality: {src.quality_score:.2f})\n"
            f"EXTRACTED CONTENT:\n{doc_text}\n"
        )
    return "\n".join(parts)
