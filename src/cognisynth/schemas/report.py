"""
Pydantic schemas for reports, versions, verification results, and conflicts.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid
from pydantic import BaseModel, Field


class ConflictSeverity(str, Enum):
    LOW = "low"          # Minor nuance/framing difference
    MEDIUM = "medium"    # Numerical or timeline discrepancy
    HIGH = "high"        # Direct factual contradiction


class Conflict(BaseModel):
    """An explicit contradiction detected between two or more claims/sources."""

    conflict_id: str = Field(default_factory=lambda: f"cnf_{uuid.uuid4().hex[:8]}")
    claim_refs: list[str] = Field(default_factory=list)  # claim_ids involved
    explanation: str
    severity: ConflictSeverity = ConflictSeverity.MEDIUM
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VerificationResult(BaseModel):
    """Detailed verification record for a claim or report section."""

    verification_id: str = Field(default_factory=lambda: f"ver_{uuid.uuid4().hex[:8]}")
    claim_id: str
    is_verified: bool
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence_count: int = 0
    refuting_evidence_count: int = 0
    reasoning: str
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReportVersion(BaseModel):
    """A versioned snapshot of a research report with change summary."""

    report_id: str = Field(default_factory=lambda: f"rep_{uuid.uuid4().hex[:8]}")
    version: int = 1
    title: str
    markdown_content: str
    claims: list[str] = Field(default_factory=list)      # claim_ids included
    citations: list[str] = Field(default_factory=list)   # source_ids cited
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    change_summary: Optional[str] = None                # Diff/delta from previous version


class Report(BaseModel):
    """Comprehensive finalized research report with full audit metadata."""

    report_id: str = Field(default_factory=lambda: f"rep_{uuid.uuid4().hex[:8]}")
    run_id: str
    title: str
    executive_summary: str
    content: str
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    confidence_rationale: str = ""
    claims_count: int = 0
    sources_count: int = 0
    conflicts: list[Conflict] = Field(default_factory=list)
    qa_review: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
