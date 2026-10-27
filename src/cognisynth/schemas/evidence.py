"""
Pydantic schemas for evidence objects, claims, sources, and documents.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    ACADEMIC = "academic"
    GOVERNMENT = "government"
    NEWS = "news"
    TECHNICAL_DOCS = "technical_docs"
    BLOG = "blog"
    GENERAL_WEB = "general_web"


class ClaimStatus(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    CONTESTED = "contested"
    REFUTED = "refuted"


class ClaimType(str, Enum):
    FACTUAL = "factual"
    STATISTICAL = "statistical"
    PREDICTIVE = "predictive"
    OPINION = "opinion"


class Source(BaseModel):
    """A web or literature source referenced in the research."""

    source_id: str = Field(default_factory=lambda: f"src_{uuid.uuid4().hex[:8]}")
    url: str
    title: str = "Untitled Source"
    domain: str = ""
    publisher: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_type: SourceType = SourceType.GENERAL_WEB
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """Raw or cleaned text document extracted from a source."""

    document_id: str = Field(default_factory=lambda: f"doc_{uuid.uuid4().hex[:8]}")
    source_id: str
    text: str
    extraction_method: str = "readability-lxml"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    char_count: int = 0

    def model_post_init(self, __context: Any) -> None:
        if not self.char_count and self.text:
            self.char_count = len(self.text)


class Evidence(BaseModel):
    """A concrete textual excerpt linking a source to a claim."""

    evidence_id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    claim_id: Optional[str] = None
    source_id: str
    snippet: str
    relevance: float = Field(default=0.8, ge=0.0, le=1.0)
    directness: float = Field(default=0.8, ge=0.0, le=1.0)  # Direct quote vs indirect inference
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Claim(BaseModel):
    """An atomic factual or statistical proposition extracted from research data."""

    claim_id: str = Field(default_factory=lambda: f"clm_{uuid.uuid4().hex[:8]}")
    text: str
    type: ClaimType = ClaimType.FACTUAL
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    status: ClaimStatus = ClaimStatus.UNVERIFIED
    evidence_refs: list[str] = Field(default_factory=list)  # list of evidence_ids
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    verification_notes: Optional[str] = None
