"""
Unit tests for claim and evidence verification and confidence calculation.
"""

import sys
import unittest
from pathlib import Path

src_path = str(Path(__file__).resolve().parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cognisynth.schemas.evidence import Source, Claim, Evidence, Document, ClaimStatus
from cognisynth.schemas.report import Conflict, ConflictSeverity
from cognisynth.evidence.verifier import verify_claims_against_evidence, compute_derived_confidence
from cognisynth.evidence.extractor import _heuristic_claim_extraction


class TestEvidenceVerification(unittest.TestCase):
    def test_heuristic_extraction(self):
        src = Source(url="https://example.com/test", domain="example.com")
        doc = Document(
            source_id=src.source_id,
            text="The new algorithm demonstrated a 45% increase in throughput during high load. System latency remained under 10ms throughout the benchmark test.",
        )

        claims, evidences = _heuristic_claim_extraction(src, doc)
        self.assertGreaterEqual(len(claims), 1)
        self.assertGreaterEqual(len(evidences), 1)
        self.assertEqual(claims[0].evidence_refs[0], evidences[0].evidence_id)

    def test_confidence_computation_without_fabrication(self):
        src = Source(url="https://example.com", quality_score=0.9)
        ev = Evidence(source_id=src.source_id, snippet="Snippet")
        c1 = Claim(text="Claim 1", status=ClaimStatus.VERIFIED, evidence_refs=[ev.evidence_id])
        c2 = Claim(text="Claim 2", status=ClaimStatus.VERIFIED, evidence_refs=[ev.evidence_id])

        conf, rationale = compute_derived_confidence([c1, c2], [src], [])
        self.assertGreater(conf, 0.8)
        self.assertIn("100% coverage", rationale)

        # Introduce a high conflict and check penalty
        conflict = Conflict(claim_refs=[c1.claim_id, c2.claim_id], explanation="Dispute", severity=ConflictSeverity.HIGH)
        penalized_conf, penalized_rationale = compute_derived_confidence([c1, c2], [src], [conflict])
        self.assertLess(penalized_conf, conf)


if __name__ == "__main__":
    unittest.main()
