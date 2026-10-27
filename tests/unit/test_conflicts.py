"""
Unit tests for contradiction and conflict detection.
"""

import sys
import unittest
from pathlib import Path

src_path = str(Path(__file__).resolve().parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cognisynth.schemas.evidence import Claim, ClaimType
from cognisynth.evidence.conflicts import detect_heuristic_contradictions
from cognisynth.schemas.report import ConflictSeverity


class TestConflictDetection(unittest.TestCase):
    def test_detect_numerical_contradiction(self):
        c1 = Claim(
            text="Global autonomous vehicle market reached $50 billion in 2024 revenue.",
            type=ClaimType.STATISTICAL,
        )
        c2 = Claim(
            text="Global autonomous vehicle market reached $12 billion in 2024 revenue.",
            type=ClaimType.STATISTICAL,
        )

        conflicts = detect_heuristic_contradictions([c1, c2])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].severity, ConflictSeverity.HIGH)
        self.assertIn(c1.claim_id, conflicts[0].claim_refs)
        self.assertIn(c2.claim_id, conflicts[0].claim_refs)

    def test_detect_polarity_contradiction(self):
        c1 = Claim(text="The new battery chemistry showed significant increase in stability.", type=ClaimType.FACTUAL)
        c2 = Claim(text="The new battery chemistry showed dangerous decrease in stability.", type=ClaimType.FACTUAL)

        conflicts = detect_heuristic_contradictions([c1, c2])
        self.assertGreaterEqual(len(conflicts), 1)


if __name__ == "__main__":
    unittest.main()
