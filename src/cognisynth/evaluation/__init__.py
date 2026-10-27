"""
Evaluation module re-exports.
"""

from cognisynth.evaluation.metrics import (
    compute_citation_accuracy,
    compute_claim_grounding,
    compute_unsupported_claim_rate,
    evaluate_research_run,
)
from cognisynth.evaluation.benchmark import run_offline_benchmark

__all__ = [
    "compute_citation_accuracy",
    "compute_claim_grounding",
    "compute_unsupported_claim_rate",
    "evaluate_research_run",
    "run_offline_benchmark",
]
