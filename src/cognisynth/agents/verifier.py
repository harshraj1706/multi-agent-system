"""
Verifier Agent.
Conducts rigorous claim verification, tests propositions against source evidence,
and calculates non-fabricated confidence metrics.
"""

from cognisynth.logging_config import logger
from cognisynth.schemas.evidence import Source, Claim, Evidence
from cognisynth.schemas.report import Conflict, VerificationResult
from cognisynth.evidence.verifier import verify_claims_against_evidence, compute_derived_confidence
from cognisynth.evidence.conflicts import detect_contradictions_llm


class VerifierAgent:
    """Agent validating claim correctness, detecting conflicts, and deriving confidence."""

    def verify_research(
        self,
        claims: list[Claim],
        evidence_items: list[Evidence],
        sources: list[Source],
    ) -> tuple[list[VerificationResult], list[Conflict], float, str]:
        """
        Verify claims, detect contradictions, and compute explainable confidence.
        """
        logger.info(f"[VerifierAgent] Verifying {len(claims)} claims against {len(evidence_items)} evidence snippets.")
        sources_map = {s.source_id: s for s in sources}

        # 1. Verify individual claims
        verification_results = verify_claims_against_evidence(claims, evidence_items, sources_map)

        # 2. Detect contradictions
        conflicts = detect_contradictions_llm(claims, sources_map)

        # 3. Calculate derived confidence
        confidence_score, confidence_rationale = compute_derived_confidence(claims, sources, conflicts)

        logger.info(f"[VerifierAgent] Verification completed. Confidence: {confidence_score:.2f} ({len(conflicts)} conflicts).")
        return verification_results, conflicts, confidence_score, confidence_rationale
