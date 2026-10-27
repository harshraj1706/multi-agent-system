"""
Unit tests for VectorStore and ResearchRepository.
"""

import sys
import unittest
import tempfile
from pathlib import Path

src_path = str(Path(__file__).resolve().parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cognisynth.memory.vector_store import LocalVectorStore
from cognisynth.memory.repository import ResearchRepository
from cognisynth.schemas.report import Report


class TestMemoryAndPersistence(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.vec_path = Path(self.tmp_dir.name) / "test_vec.json"
        self.repo_path = Path(self.tmp_dir.name) / "test_repo.json"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_vector_store_semantic_search(self):
        vs = LocalVectorStore(storage_path=self.vec_path)
        vs.add_document("Quantum computing utilizes superposition and entanglement for computational speedup.", metadata={"tag": "quantum"})
        vs.add_document("Deep neural networks with transformer architecture achieve state of the art in NLP.", metadata={"tag": "nlp"})
        vs.add_document("CRISPR gene editing allows targeted genomic modifications.", metadata={"tag": "bio"})

        # Search for quantum
        results = vs.similarity_search("quantum entanglement superposition", top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metadata"]["tag"], "quantum")
        self.assertGreater(results[0]["similarity_score"], 0.2)

    def test_repository_version_diffing(self):
        repo = ResearchRepository(storage_path=self.repo_path)
        r1 = Report(
            run_id="run_101",
            title="AI Safety Report",
            executive_summary="v1 summary",
            content="# AI Safety v1",
            confidence_score=0.80,
        )
        v1 = repo.save_report(r1, claims_list=["clm_1", "clm_2"], citations_list=["src_1"])
        self.assertEqual(v1.version, 1)

        # Create v2 with updated claim and higher confidence
        r2 = Report(
            run_id="run_101",
            title="AI Safety Report v2",
            executive_summary="v2 summary",
            content="# AI Safety v2",
            confidence_score=0.88,
        )
        v2 = repo.save_report(r2, claims_list=["clm_1", "clm_2", "clm_3"], citations_list=["src_1", "src_2"])
        self.assertEqual(v2.version, 2)
        self.assertIn("+1 new claims", v2.change_summary)
        self.assertIn("Confidence delta: +0.08", v2.change_summary)


if __name__ == "__main__":
    unittest.main()
