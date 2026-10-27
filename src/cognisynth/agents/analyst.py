"""
Analyst Agent.
Synthesizes raw evidence, extracted claims, and source materials into
rigorous, structured technical reasoning and multi-perspective insights.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from cognisynth.logging_config import logger
from cognisynth.schemas.evidence import Source, Document, Claim
from cognisynth.tools.llm import _message_text
from cognisynth.tools.model_router import get_model_router


ANALYST_SYSTEM_PROMPT = """You are the Principal Decision Intelligence Analyst for CogniSynth.
Your role is to analyze verified claims, source evidence, and multi-domain data to synthesize deep technical insights.

Core Instructions:
1. Ground every analysis point in the provided evidence.
2. Highlight empirical facts, real-world benchmarks, and concrete mechanisms.
3. Compare differing perspectives objectively.
4. Structure your synthesis into logical sections (Core Drivers, Architectural Analysis, Trade-offs & Limitations, Outlook).
"""


class AnalystAgent:
    """Agent that performs multi-source synthesis and technical reasoning."""

    def analyze(
        self,
        query: str,
        claims: list[Claim],
        sources: list[Source],
        documents: list[Document],
    ) -> str:
        """Synthesize findings from claims and evidence into detailed thematic analysis."""
        logger.info(f"[AnalystAgent] Analyzing {len(claims)} claims and {len(sources)} sources for: {query}")

        claims_text = "\n".join(
            [f"- [{c.type.value.upper()}] {c.text} (Confidence: {c.confidence:.2f})" for c in claims[:12]]
        )
        sources_text = "\n".join(
            [f"- [{s.source_type.value}] {s.title} ({s.url}) - Quality: {s.quality_score:.2f}" for s in sources[:6]]
        )

        llm = get_model_router().get_reasoning_model()
        messages = [
            SystemMessage(content=ANALYST_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Research Query: {query}\n\n"
                    f"Verified Claims:\n{claims_text}\n\n"
                    f"Authoritative Sources:\n{sources_text}\n\n"
                    "Synthesize a thorough, cohesive technical analysis."
                )
            ),
        ]

        try:
            response = llm.invoke(messages)
            return _message_text(response).strip()
        except Exception as exc:
            logger.error(f"[AnalystAgent] LLM synthesis failed: {exc}")
            return f"Analysis synthesis fallback: Topic investigated with {len(claims)} claims across {len(sources)} sources."
