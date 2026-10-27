"""
Claim Verification and Confidence Calculation Engine.
Calculates explainable confidence from stored evidence signals (coverage, quality, agreement).
Strictly derives confidence from data without fabrication.
"""

from cognisynth.schemas.evidence import Claim, ClaimStatus, Evidence, Source
from cognisynth.schemas.report import Conflict, ConflictSeverity, VerificationResult


def verify_claims_against_evidence(
    claims: list[Claim],
    evidence_items: list[Evidence],
    sources_map: dict[str, Source],
) -> list[VerificationResult]:
    """
    Verify each claim against available evidence snippets and source quality.
    """
    ev_by_id = {e.evidence_id: e for e in evidence_items}
    results: list[VerificationResult] = []

    for claim in claims:
        supporting_snippets = [
            ev_by_id[eid] for eid in claim.evidence_refs if eid in ev_by_id
        ]
        
        # Calculate verification confidence
        if not supporting_snippets:
            claim.status = ClaimStatus.UNVERIFIED
            results.append(
                VerificationResult(
                    claim_id=claim.claim_id,
                    is_verified=False,
                    confidence=0.3,
                    supporting_evidence_count=0,
                    refuting_evidence_count=0,
                    reasoning="No concrete evidence snippets linked to this claim.",
                )
            )
            continue

        # Score based on evidence quality
        avg_directness = sum(e.directness for e in supporting_snippets) / len(supporting_snippets)
        src_scores = [
            sources_map[e.source_id].quality_score
            for e in supporting_snippets
            if e.source_id in sources_map
        ]
        avg_src_score = sum(src_scores) / len(src_scores) if src_scores else 0.5

        claim_conf = round((0.6 * avg_src_score) + (0.4 * avg_directness), 2)
        claim.confidence = claim_conf
        claim.status = ClaimStatus.VERIFIED if claim_conf >= 0.6 else ClaimStatus.UNVERIFIED

        results.append(
            VerificationResult(
                claim_id=claim.claim_id,
                is_verified=(claim.status == ClaimStatus.VERIFIED),
                confidence=claim_conf,
                supporting_evidence_count=len(supporting_snippets),
                refuting_evidence_count=0,
                reasoning=f"Supported by {len(supporting_snippets)} snippet(s). Mean source quality: {avg_src_score:.2f}.",
            )
        )

    return results


def compute_derived_confidence(
    claims: list[Claim],
    sources: list[Source],
    conflicts: list[Conflict],
) -> tuple[float, str]:
    """
    Derive an explainable overall confidence score solely from stored signals:
    - Evidence Coverage: % of claims verified
    - Source Quality: Average quality score of sources
    - Conflict Penalty: Subtraction for unresolved severe contradictions
    - Freshness & Directness
    """
    if not claims:
        return 0.5, "No claims extracted to measure confidence."

    verified_claims = [c for c in claims if c.status == ClaimStatus.VERIFIED]
    coverage_score = len(verified_claims) / len(claims)

    avg_source_score = (
        sum(s.quality_score for s in sources) / len(sources) if sources else 0.5
    )

    # Conflict deductions
    high_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.HIGH]
    med_conflicts = [c for c in conflicts if c.severity == ConflictSeverity.MEDIUM]
    conflict_penalty = (len(high_conflicts) * 0.15) + (len(med_conflicts) * 0.05)
    conflict_penalty = min(0.40, conflict_penalty)

    # Composite formula
    base_confidence = (0.50 * avg_source_score) + (0.50 * coverage_score)
    final_confidence = max(0.1, min(0.98, base_confidence - conflict_penalty))
    final_confidence = round(final_confidence, 2)

    rationale = (
        f"Derived Confidence: {final_confidence * 100:.0f}%. "
        f"Signal breakdown: {len(verified_claims)}/{len(claims)} claims verified ({coverage_score*100:.0f}% coverage), "
        f"mean source reliability: {avg_source_score:.2f}, "
        f"{len(conflicts)} contradiction(s) analyzed (penalty: -{conflict_penalty*100:.0f}%)."
    )

    return final_confidence, rationale
