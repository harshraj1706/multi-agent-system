"""
Source quality scoring engine.
Evaluates domain authority, freshness, directness, and extraction quality.
"""

from urllib.parse import urlparse
from cognisynth.schemas.evidence import Source, SourceType, Document


# Authority weights by known domain patterns
HIGH_AUTHORITY_DOMAINS = {
    "arxiv.org": 0.95,
    "nature.com": 0.95,
    "ieee.org": 0.95,
    "acm.org": 0.95,
    "github.com": 0.88,
    "reuters.com": 0.90,
    "bloomberg.com": 0.90,
    "bbc.com": 0.88,
    "nytimes.com": 0.88,
    "wsj.com": 0.90,
}

AUTHORITY_BY_TYPE = {
    SourceType.ACADEMIC: 0.92,
    SourceType.GOVERNMENT: 0.90,
    SourceType.TECHNICAL_DOCS: 0.85,
    SourceType.NEWS: 0.80,
    SourceType.BLOG: 0.60,
    SourceType.GENERAL_WEB: 0.50,
}


def score_source_authority(source: Source) -> float:
    """Evaluate publisher/domain authority."""
    domain = source.domain.lower()
    for auth_dom, score in HIGH_AUTHORITY_DOMAINS.items():
        if auth_dom in domain:
            return score
    return AUTHORITY_BY_TYPE.get(source.source_type, 0.55)


def score_extraction_quality(document: Document) -> float:
    """Evaluate content extraction depth and readability."""
    if not document or not document.text:
        return 0.1
    length = len(document.text)
    if length > 3000:
        return 0.95
    if length > 1500:
        return 0.85
    if length > 500:
        return 0.70
    if length > 100:
        return 0.40
    return 0.15


def score_source(source: Source, document: Document) -> float:
    """
    Calculate composite quality score:
    Quality = 0.55 * Authority + 0.30 * Extraction Quality + 0.15 * Base Directness.
    """
    authority = score_source_authority(source)
    extraction = score_extraction_quality(document)
    directness = 0.85 if source.source_type in (SourceType.TECHNICAL_DOCS, SourceType.ACADEMIC) else 0.70

    composite = (0.55 * authority) + (0.30 * extraction) + (0.15 * directness)
    source.quality_score = round(min(1.0, max(0.1, composite)), 3)
    return source.quality_score
