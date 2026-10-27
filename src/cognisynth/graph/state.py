"""
Graph state schema for LangGraph execution of CogniSynth workflows.
"""

from typing import Annotated, Any, Optional, TypedDict
import operator

from cognisynth.schemas.research import ResearchPlan, ResearchRun
from cognisynth.schemas.evidence import Source, Document, Claim, Evidence
from cognisynth.schemas.report import Conflict, Report


class ResearchGraphState(TypedDict, total=False):
    """Execution state passed between nodes in the CogniSynth graph."""

    run_id: str
    query: str
    plan: Optional[ResearchPlan]
    sources: list[Source]
    documents: list[Document]
    claims: list[Claim]
    evidence_items: list[Evidence]
    conflicts: list[Conflict]
    report_content: str
    qa_review: str
    confidence_score: float
    confidence_rationale: str
    status: str
    requires_approval: bool
    is_approved: bool
    metrics: dict[str, Any]
    errors: list[str]
    current_step: str
