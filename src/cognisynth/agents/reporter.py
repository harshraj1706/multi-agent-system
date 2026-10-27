"""
Reporter Agent.
Synthesizes verified claims, analysis, and citations into a publishable,
evidence-grounded research report with auditable footnotes.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from cognisynth.logging_config import logger
from cognisynth.schemas.evidence import Source, Claim
from cognisynth.schemas.report import Conflict, Report
from cognisynth.tools.llm import _message_text
from cognisynth.tools.model_router import get_model_router


REPORTER_SYSTEM_PROMPT = """You are the Lead Scientific & Technical Reporter for CogniSynth.
Your role is to produce a comprehensive, structured, publication-grade research report.

Report Structure Guidelines:
# [Report Title]
## Executive Summary
## Strategic & Technical Overview
## Deep Technical Analysis & Findings
## Empirical Evidence & Benchmark Results
## Trade-offs, Vulnerabilities & Limitations
## Strategic Outlook & Recommendations
## Citations & Evidence Provenance

Instructions:
- Write with exceptional clarity, precision, and depth.
- Incorporate in-text citations linking to source IDs (e.g., [Source: Title](URL)).
- Do not make unsupported factual assertions.
- Clearly present differing evidence if conflicts exist.
"""


class ReporterAgent:
    """Agent synthesizing the final structured research report with citations."""

    def generate_report(
        self,
        run_id: str,
        query: str,
        analysis_text: str,
        claims: list[Claim],
        sources: list[Source],
        conflicts: list[Conflict],
        confidence_score: float,
        confidence_rationale: str,
    ) -> Report:
        """Synthesize final report with grounded citations."""
        logger.info(f"[ReporterAgent] Compiling report for run {run_id}: '{query}'")

        sources_table = "\n".join(
            [f"- [{idx}] [{s.title}]({s.url}) — Domain: `{s.domain}`, Quality: `{s.quality_score:.2f}`" for idx, s in enumerate(sources, start=1)]
        )

        claims_summary = "\n".join(
            [f"- [{c.status.value.upper()}] {c.text} (Confidence: {c.confidence:.2f})" for c in claims[:12]]
        )

        prompt = (
            f"Research Topic: {query}\n\n"
            f"Key Verified Claims:\n{claims_summary}\n\n"
            f"Thematic Analysis:\n{analysis_text[:3500]}\n\n"
            f"Authoritative Sources:\n{sources_table}\n\n"
            f"Confidence Score: {confidence_score*100:.0f}%\n"
            f"Rationale: {confidence_rationale}\n\n"
            "Generate the complete, publication-ready research report in Markdown."
        )

        llm = get_model_router().get_judge_model()
        messages = [
            SystemMessage(content=REPORTER_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        try:
            resp = llm.invoke(messages)
            content = _message_text(resp).strip()
        except Exception as exc:
            logger.error(f"[ReporterAgent] Generation failed ({exc}); using fallback template.")
            content = (
                f"# Autonomous Research Report: {query}\n\n"
                f"## Executive Summary\n\n"
                f"This report synthesizes intelligence gathered across {len(sources)} sources with {confidence_score*100:.0f}% confidence.\n\n"
                f"## Analysis\n\n{analysis_text}\n\n"
                f"## Verified Claims\n\n{claims_summary}\n\n"
                f"## Sources\n\n{sources_table}"
            )

        # Extract title and executive summary
        lines = content.split("\n")
        title = lines[0].replace("#", "").strip() if lines else f"Research Report: {query}"
        summary = f"Comprehensive decision-intelligence analysis on {query} based on {len(sources)} verified sources."

        return Report(
            run_id=run_id,
            title=title,
            executive_summary=summary,
            content=content,
            confidence_score=confidence_score,
            confidence_rationale=confidence_rationale,
            claims_count=len(claims),
            sources_count=len(sources),
            conflicts=conflicts,
        )
