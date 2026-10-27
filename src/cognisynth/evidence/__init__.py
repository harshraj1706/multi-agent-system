"""
Evidence intelligence module re-exports.
"""

from cognisynth.evidence.scorer import score_source, score_source_authority, score_extraction_quality
from cognisynth.evidence.extractor import extract_claims_and_evidence
from cognisynth.evidence.conflicts import detect_heuristic_contradictions, detect_contradictions_llm
from cognisynth.evidence.verifier import verify_claims_against_evidence, compute_derived_confidence

__all__ = [
    "score_source",
    "score_source_authority",
    "score_extraction_quality",
    "extract_claims_and_evidence",
    "detect_heuristic_contradictions",
    "detect_contradictions_llm",
    "verify_claims_against_evidence",
    "compute_derived_confidence",
]
