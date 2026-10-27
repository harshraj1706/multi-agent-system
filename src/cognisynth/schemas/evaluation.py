"""
Pydantic schemas for benchmark cases and evaluation metrics.
"""

from datetime import datetime, timezone
from typing import Any, Optional
import uuid
from pydantic import BaseModel, Field


class BenchmarkCase(BaseModel):
    """Benchmark test case for research evaluation."""

    case_id: str = Field(default_factory=lambda: f"case_{uuid.uuid4().hex[:6]}")
    query: str
    domain: str = "technology"
    expected_entities: list[str] = Field(default_factory=list)
    key_questions: list[str] = Field(default_factory=list)
    known_contradictions: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    """Reproducible evaluation results measuring research quality and performance."""

    eval_id: str = Field(default_factory=lambda: f"eval_{uuid.uuid4().hex[:8]}")
    run_id: str
    citation_accuracy: float = Field(default=1.0, ge=0.0, le=1.0)
    grounding: float = Field(default=0.85, ge=0.0, le=1.0)
    source_recall: float = Field(default=0.8, ge=0.0, le=1.0)
    unsupported_claim_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    latency: float = Field(default=0.0, ge=0.0)  # Total seconds
    cost: float = Field(default=0.0, ge=0.0)     # Estimated USD cost
    claims_evaluated: int = 0
    sources_evaluated: int = 0
    evaluation_notes: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
