"""
Unit tests for CogniSynth Pydantic data schemas.
"""

import sys
import unittest
from pathlib import Path

# Add src to python path for testing
src_path = str(Path(__file__).resolve().parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cognisynth.schemas import (
    ResearchRequest,
    ResearchPlan,
    ResearchTask,
    ResearchRun,
    TaskStatus,
    TaskType,
    Source,
    Document,
    Claim,
    Evidence,
    Conflict,
    ConflictSeverity,
    VerificationResult,
    ReportVersion,
    Report,
    EvaluationResult,
    BenchmarkCase,
)


class TestSchemas(unittest.TestCase):
    def test_research_task_and_plan(self):
        t1 = ResearchTask(objective="Task 1", type=TaskType.SEARCH)
        t2 = ResearchTask(objective="Task 2", type=TaskType.SYNTHESIZE, dependencies=[t1.task_id])
        plan = ResearchPlan(objective="Test Plan", tasks=[t1, t2])

        self.assertEqual(len(plan.tasks), 2)
        # Only t1 should be ready initially
        ready = plan.ready_tasks()
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0].task_id, t1.task_id)

        # Mark t1 as completed
        t1.status = TaskStatus.COMPLETED
        ready_after = plan.ready_tasks()
        self.assertEqual(len(ready_after), 1)
        self.assertEqual(ready_after[0].task_id, t2.task_id)

    def test_source_and_document(self):
        src = Source(url="https://example.com/ai", domain="example.com", quality_score=0.9)
        doc = Document(source_id=src.source_id, text="AI is evolving rapidly.")

        self.assertTrue(src.source_id.startswith("src_"))
        self.assertTrue(doc.document_id.startswith("doc_"))
        self.assertEqual(doc.char_count, len(doc.text))

    def test_claim_and_evidence(self):
        ev = Evidence(source_id="src_1", snippet="Quantum computing reached 1000 qubits.", relevance=0.95)
        claim = Claim(text="Quantum computers exceed 1000 qubits.", evidence_refs=[ev.evidence_id], confidence=0.92)

        self.assertEqual(claim.evidence_refs, [ev.evidence_id])
        self.assertAlmostEqual(claim.confidence, 0.92)

    def test_conflict_and_report(self):
        conflict = Conflict(
            claim_refs=["clm_1", "clm_2"],
            explanation="Source A claims 10x speedup while Source B measured 2x.",
            severity=ConflictSeverity.HIGH,
        )
        report = Report(
            run_id="run_123",
            title="Quantum Benchmark Report",
            executive_summary="Executive summary here",
            content="# Report Content",
            conflicts=[conflict],
        )

        self.assertEqual(len(report.conflicts), 1)
        self.assertEqual(report.conflicts[0].severity, ConflictSeverity.HIGH)


if __name__ == "__main__":
    unittest.main()
