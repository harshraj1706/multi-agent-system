"""
Scraper Agent.
Coordinates deep content extraction from specified URLs and normalizes text.
"""

from cognisynth.logging_config import logger
from cognisynth.schemas.evidence import Document
from cognisynth.tools.scraper import extract_main_content


class ScraperAgent:
    """Agent specialized in full-text web document extraction."""

    def scrape_url(self, url: str, source_id: str = "src_manual") -> Document:
        """Extract sanitized document text from a URL."""
        logger.info(f"[ScraperAgent] Scraping URL: {url}")
        return extract_main_content(url, source_id=source_id)
