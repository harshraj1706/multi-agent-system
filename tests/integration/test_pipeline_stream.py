"""
Integration tests for streaming research pipeline.
Mocked LLM & Search to ensure fast, deterministic offline execution.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

src_path = str(Path(__file__).resolve().parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cognisynth.services.research_service import ResearchService
from cognisynth.schemas.research import ResearchPlan, ResearchTask, TaskType
from cognisynth.schemas.evidence import Source, Document, Claim, Evidence, SourceType, ClaimStatus
from cognisynth.schemas.report import Report


class TestPipelineStream(unittest.TestCase):
    @patch("cognisynth.services.research_service.PlannerAgent.plan")
    @patch("cognisynth.services.research_service.ResearcherAgent.execute_task")
    @patch("cognisynth.services.research_service.extract_claims_and_evidence")
    @patch("cognisynth.services.research_service.VerifierAgent.verify_research")
    @patch("cognisynth.services.research_service.AnalystAgent.analyze")
    @patch("cognisynth.services.research_service.ReporterAgent.generate_report")
    @patch("cognisynth.services.research_service.CriticAgent.review")
    def test_pipeline_stream_emits_structured_events(
        self, mock_review, mock_report, mock_analyze, mock_verify, mock_extract, mock_execute, mock_plan
    ):
        # 1. Mock Plan
        t1 = ResearchTask(task_id="t1", type=TaskType.SEARCH, objective="Search AI")
        mock_plan.return_value = ResearchPlan(objective="Edge AI", tasks=[t1])

        # 2. Mock Researcher
        src = Source(
            url="https://example.com/ai",
            title="Test AI",
            domain="example.com",
            source_type=SourceType.TECHNICAL_DOCS,
            quality_score=0.85,
        )
        doc = Document(source_id=src.source_id, text="The system increased performance by 30 percent in production.")
        mock_execute.return_value = ([src], [doc])

        # 3. Mock Claims & Evidence
        ev = Evidence(source_id=src.source_id, snippet="Increased performance by 30 percent.")
        clm = Claim(text="Performance increased by 30%.", status=ClaimStatus.VERIFIED, evidence_refs=[ev.evidence_id])
        mock_extract.return_value = ([clm], [ev])

        # 4. Mock Verifier
        mock_verify.return_value = ([], [], 0.92, "High coverage")

        # 5. Mock Analyst
        mock_analyze.return_value = "Detailed analysis of AI performance."

        # 6. Mock Reporter with real Report object
        mock_report.return_value = Report(
            run_id="run_test",
            title="Edge AI Deployment Analysis",
            executive_summary="Executive summary of edge AI",
            content="# Edge AI Deployment Report\n\nFull analysis content.",
            confidence_score=0.92,
        )

        # 7. Mock Critic
        mock_review.return_value = "QA Review: 9/10"

        service = ResearchService()
        events = list(service.run_research_stream("Edge AI deployment", max_sources=2))

        self.assertGreater(len(events), 5)
        parsed_types = [json.loads(e)["type"] for e in events if e.strip()]

        self.assertIn("status", parsed_types)
        self.assertIn("log", parsed_types)
        self.assertIn("plan", parsed_types)
        self.assertIn("sources", parsed_types)
        self.assertIn("claims", parsed_types)
        self.assertIn("metric", parsed_types)
        self.assertIn("complete", parsed_types)


if __name__ == "__main__":
    unittest.main()
