"""
Evaluation and benchmark test suite.
"""

import sys
import unittest
from pathlib import Path

src_path = str(Path(__file__).resolve().parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cognisynth.evaluation.benchmark import run_offline_benchmark


class TestEvaluationBenchmark(unittest.TestCase):
    def test_run_offline_benchmark(self):
        results = run_offline_benchmark()
        self.assertGreaterEqual(len(results), 4)

        for res in results:
            self.assertGreaterEqual(res["grounding"], 0.80)
            self.assertGreaterEqual(res["citation_accuracy"], 0.80)
            self.assertLessEqual(res["unsupported_claim_rate"], 0.20)
            self.assertGreater(res["latency"], 0.0)


if __name__ == "__main__":
    unittest.main()
