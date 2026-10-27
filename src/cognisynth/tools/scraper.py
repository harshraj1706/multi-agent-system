"""
Web content extraction adapter using Readability and BeautifulSoup.
Converts arbitrary HTML into clean, structured Document instances.
"""

import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from readability import Document as ReadabilityDoc

from cognisynth.config import settings
from cognisynth.logging_config import logger
from cognisynth.schemas.evidence import Document


def extract_main_content(url: str, source_id: str = "src_direct") -> Document:
    """
    Extract readable article text from a URL and package as a structured Document.
    """
    if not url or not url.strip():
        return Document(
            source_id=source_id,
            text="Could not scrape page: missing URL.",
            extraction_method="readability-lxml",
        )

    url = url.strip()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/124.0 Safari/537.36 CogniSynth/1.0"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        doc = ReadabilityDoc(response.text)
        soup = BeautifulSoup(doc.summary(), "html.parser")

        # Strip scripts, styles, media, and interactive controls
        for tag in soup(["script", "style", "iframe", "img", "svg", "video", "audio", "form", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text("\n", strip=True)
        text = re.sub(r"\n\s*\n+", "\n\n", text)

        if not text:
            return Document(
                source_id=source_id,
                text="Could not scrape page: no readable article text found.",
                extraction_method="readability-lxml",
            )

        truncated_text = text[: settings.max_scraped_chars]
        return Document(
            source_id=source_id,
            text=truncated_text,
            extraction_method="readability-lxml",
            char_count=len(truncated_text),
        )

    except requests.RequestException as exc:
        logger.warning(f"HTTP request error scraping {url}: {exc}")
        return Document(
            source_id=source_id,
            text=f"Could not scrape page: request failed ({exc}).",
            extraction_method="failed_http",
        )
    except Exception as exc:
        logger.warning(f"Unexpected error scraping {url}: {exc}")
        return Document(
            source_id=source_id,
            text=f"Could not scrape page: {exc}.",
            extraction_method="failed_parser",
        )
