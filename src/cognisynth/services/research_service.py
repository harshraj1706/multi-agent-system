"""
CogniSynth Master Research Service.
Orchestrates end-to-end autonomous research, dynamic planning, evidence grounding,
verification, persistence, and real-time streaming telemetry.
"""

import os
import re
import time
import uuid
from typing import Generator, Optional

from cognisynth.config import settings
from cognisynth.logging_config import logger
from cognisynth.schemas.research import ResearchRequest, ResearchRun, ResearchPlan, TaskStatus, RunStatus
from cognisynth.schemas.evidence import Source, Document, Claim, Evidence
from cognisynth.schemas.report import Report, Conflict
from cognisynth.agents.planner import PlannerAgent
from cognisynth.agents.researcher import ResearcherAgent
from cognisynth.agents.analyst import AnalystAgent
from cognisynth.agents.verifier import VerifierAgent
from cognisynth.agents.reporter import ReporterAgent
from cognisynth.agents.critic import CriticAgent
from cognisynth.evidence.extractor import extract_claims_and_evidence
from cognisynth.memory.vector_store import get_vector_store
from cognisynth.memory.repository import get_repository
from cognisynth.observability.events import StreamEvent
from cognisynth.observability.tracing import RunTracer
from cognisynth.observability.cost import CostTracker


class ResearchService:
    """Enterprise service coordinating the full CogniSynth research lifecycle."""

    def __init__(self):
        self.planner = PlannerAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.verifier = VerifierAgent()
        self.reporter = ReporterAgent()
        self.critic = CriticAgent()
        self.repo = get_repository()
        self.vector_store = get_vector_store()

    def run_research_stream(
        self,
        topic: str,
        run_id: Optional[str] = None,
        max_sources: int = 4,
    ) -> Generator[str, None, None]:
        """
        Execute the full dynamic research workflow while yielding typed, structured SSE events.
        Compatible with both legacy stream consumers and enhanced dashboards.
        """
        topic = topic.strip()
        if not topic:
            yield StreamEvent.error("Research topic cannot be empty.")
            return

        run_id = run_id or f"run_{uuid.uuid4().hex[:10]}"
        run_record = ResearchRun(run_id=run_id, query=topic, status=RunStatus.EXECUTING)
        self.repo.save_run(run_record)

        tracer = RunTracer(run_id)
        cost_tracker = CostTracker()

        yield StreamEvent.status("supervisor", "Active", run_id)
        yield StreamEvent.log(f"[supervisor] CogniSynth run '{run_id}' initialized for: '{topic}'", "supervisor", run_id)

        try:
            # ==========================================
            # STEP 1 - DYNAMIC PLANNING
            # ==========================================
            span_plan = tracer.start_span("dynamic_planning", "planner")
            yield StreamEvent.status("planner", "Running", run_id)
            yield StreamEvent.log("[planner] Decomposing objective into dynamic task graph...", "planner", run_id)

            plan: ResearchPlan = self.planner.plan(topic)
            run_record.plan_id = plan.plan_id
            self.repo.save_plan(plan)
            tracer.finish_span(span_plan)

            yield StreamEvent.plan(plan.model_dump(mode="json"), run_id)
            yield StreamEvent.status("planner", "Idle", run_id)
            yield StreamEvent.log(f"[planner] Task graph created with {len(plan.tasks)} tasks.", "planner", run_id)

            # ==========================================
            # STEP 2 - PARALLEL/SEQUENTIAL RESEARCH
            # ==========================================
            span_res = tracer.start_span("evidence_gathering", "researcher")
            yield StreamEvent.status("research", "Running", run_id)

            all_sources: list[Source] = []
            all_documents: list[Document] = []

            search_tasks = [t for t in plan.tasks if t.type.value == "search"]
            for s_task in search_tasks:
                yield StreamEvent.log(f"[research] Querying angle: '{s_task.objective}'...", "research", run_id)
                srcs, docs = self.researcher.execute_task(s_task, max_results=max_sources // len(search_tasks) or 2)
                all_sources.extend(srcs)
                all_documents.extend(docs)
                cost_tracker.record_search(1)
                cost_tracker.record_scrape(len(docs))

            # Deduplicate sources by URL
            seen_urls = set()
            unique_sources: list[Source] = []
            for s in all_sources:
                if s.url and s.url not in seen_urls:
                    seen_urls.add(s.url)
                    unique_sources.append(s)

            if not unique_sources and all_sources:
                unique_sources = all_sources

            tracer.finish_span(span_res)
            yield StreamEvent.status("research", "Idle", run_id)
            yield StreamEvent.sources([s.model_dump(mode="json") for s in unique_sources], run_id)
            yield StreamEvent.metric(
                sources_count=len(unique_sources),
                pages_analyzed=len(all_documents),
                cost_usd=cost_tracker.calculate_cost(),
                latency_sec=tracer.total_latency(),
                run_id=run_id,
            )

            # ==========================================
            # STEP 3 - EVIDENCE & CLAIM EXTRACTION
            # ==========================================
            span_ext = tracer.start_span("claim_extraction", "extractor")
            yield StreamEvent.status("scraper", "Running", run_id)
            yield StreamEvent.log(f"[scraper] Extracting atomic claims from {len(unique_sources)} sources...", "scraper", run_id)

            all_claims: list[Claim] = []
            all_evidence: list[Evidence] = []
            doc_map = {d.source_id: d for d in all_documents}

            for src in unique_sources[:4]:
                doc = doc_map.get(src.source_id)
                if doc:
                    claims, evidences = extract_claims_and_evidence(src, doc, use_llm=True)
                    all_claims.extend(claims)
                    all_evidence.extend(evidences)
                    cost_tracker.record_llm_call(prompt_tokens=400, completion_tokens=150)

            tracer.finish_span(span_ext)
            yield StreamEvent.status("scraper", "Idle", run_id)
            yield StreamEvent.claims([c.model_dump(mode="json") for c in all_claims], run_id)
            yield StreamEvent.log(f"[scraper] {len(all_claims)} atomic propositions linked to evidence snippets.", "scraper", run_id)

            # ==========================================
            # STEP 4 - VERIFICATION & CONTRADICTIONS
            # ==========================================
            span_ver = tracer.start_span("verification", "verifier")
            yield StreamEvent.status("verifier", "Running", run_id)
            yield StreamEvent.log("[verifier] Cross-referencing claims and auditing for contradictions...", "verifier", run_id)

            ver_results, conflicts, confidence_score, conf_rationale = self.verifier.verify_research(
                all_claims, all_evidence, unique_sources
            )
            cost_tracker.record_llm_call(prompt_tokens=500, completion_tokens=200)

            tracer.finish_span(span_ver)
            yield StreamEvent.status("verifier", "Idle", run_id)
            if conflicts:
                yield StreamEvent.conflicts([c.model_dump(mode="json") for c in conflicts], run_id)
                yield StreamEvent.log(f"[verifier] Detected {len(conflicts)} explicit contradiction(s). Added to audit trail.", "verifier", run_id)
            else:
                yield StreamEvent.log("[verifier] No critical contradictions found across sources.", "verifier", run_id)

            yield StreamEvent.log(f"[verifier] Non-fabricated Confidence: {confidence_score*100:.0f}%.", "verifier", run_id)

            # ==========================================
            # STEP 5 - ANALYSIS & SYNTHESIS
            # ==========================================
            span_ana = tracer.start_span("analysis", "analyst")
            yield StreamEvent.status("writer", "Running", run_id)
            yield StreamEvent.log("[writer] Synthesizing comprehensive research report...", "writer", run_id)

            analysis_text = self.analyst.analyze(topic, all_claims, unique_sources, all_documents)
            cost_tracker.record_llm_call(prompt_tokens=1200, completion_tokens=800)
            tracer.finish_span(span_ana)

            # ==========================================
            # STEP 6 - FINAL REPORT SYNTHESIS
            # ==========================================
            report = self.reporter.generate_report(
                run_id=run_id,
                query=topic,
                analysis_text=analysis_text,
                claims=all_claims,
                sources=unique_sources,
                conflicts=conflicts,
                confidence_score=confidence_score,
                confidence_rationale=conf_rationale,
            )
            cost_tracker.record_llm_call(prompt_tokens=1500, completion_tokens=1000)

            # ==========================================
            # STEP 7 - CRITIC ADVERSARIAL QA
            # ==========================================
            span_crit = tracer.start_span("critique", "critic")
            yield StreamEvent.status("writer", "Idle", run_id)
            yield StreamEvent.status("reviewer", "Running", run_id)
            yield StreamEvent.log("[reviewer] Auditing report against 7 quality criteria and debate checks...", "reviewer", run_id)

            qa_feedback = self.critic.review(topic, report.content, conflicts, confidence_score)
            cost_tracker.record_llm_call(prompt_tokens=800, completion_tokens=400)
            report.qa_review = qa_feedback
            tracer.finish_span(span_crit)

            yield StreamEvent.status("reviewer", "Idle", run_id)
            yield StreamEvent.log("[reviewer] Quality Assurance audit complete.", "reviewer", run_id)

            # ==========================================
            # STEP 8 - PERSISTENCE & VECTOR MEMORY
            # ==========================================
            version_snapshot = self.repo.save_report(
                report,
                claims_list=[c.claim_id for c in all_claims],
                citations_list=[s.source_id for s in unique_sources],
            )
            run_record.status = RunStatus.COMPLETED
            run_record.final_report_id = report.report_id
            run_record.metrics = {
                "confidence_score": confidence_score,
                "sources_count": len(unique_sources),
                "claims_count": len(all_claims),
                "conflicts_count": len(conflicts),
                "latency_seconds": tracer.total_latency(),
                "cost_usd": cost_tracker.calculate_cost(),
                "trace": tracer.to_dict(),
            }
            self.repo.save_run(run_record)

            # Index into local vector store for cross-run semantic search
            self.vector_store.add_document(
                text=f"{topic}\n\n{report.executive_summary}\n\n{report.content[:1500]}",
                metadata={"run_id": run_id, "topic": topic, "report_id": report.report_id},
            )

            # Assemble finalized markdown output (maintaining backward-compatibility)
            final_report_markdown = (
                f"{report.content}\n\n"
                f"---\n\n"
                f"## Quality Assurance Review\n{qa_feedback}"
            )

            yield StreamEvent.metric(
                sources_count=len(unique_sources),
                pages_analyzed=len(all_documents),
                claims_count=len(all_claims),
                confidence_score=confidence_score,
                cost_usd=cost_tracker.calculate_cost(),
                latency_sec=tracer.total_latency(),
                run_id=run_id,
            )
            yield StreamEvent.trace(tracer.to_dict())
            yield StreamEvent.complete(
                report=final_report_markdown,
                report_id=report.report_id,
                confidence_score=confidence_score,
                run_id=run_id,
                metadata=run_record.metrics,
            )

        except Exception as exc:
            logger.error(f"Research pipeline error for '{topic}': {exc}", exc_info=True)
            yield StreamEvent.status("supervisor", "Idle", run_id)
            yield StreamEvent.status("research", "Idle", run_id)
            yield StreamEvent.status("scraper", "Idle", run_id)
            yield StreamEvent.status("writer", "Idle", run_id)
            yield StreamEvent.status("reviewer", "Idle", run_id)
            yield StreamEvent.log(f"<span style='color: #ff4b4b;'>[error] {str(exc)}</span>", "supervisor", run_id)
            yield StreamEvent.error(str(exc), run_id)


_service_instance: Optional[ResearchService] = None


def get_research_service() -> ResearchService:
    global _service_instance
    if _service_instance is None:
        _service_instance = ResearchService()
    return _service_instance
