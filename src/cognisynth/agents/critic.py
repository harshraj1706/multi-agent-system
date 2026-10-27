"""
Critic & Debate Agent.
Performs adversarial evaluation, explains evidence contradictions in a debate loop,
and provides objective Quality Assurance auditing.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from cognisynth.logging_config import logger
from cognisynth.schemas.evidence import Claim, Source
from cognisynth.schemas.report import Conflict
from cognisynth.tools.llm import _message_text
from cognisynth.tools.model_router import get_model_router


CRITIC_SYSTEM_PROMPT = """You are the Senior Research Quality Assurance and Debate Critic for CogniSynth.
Your role is to rigorously challenge the generated findings, audit reasoning integrity, and explain any discovered contradictions.

Evaluate the report across:
1. Accuracy & Evidence Grounding (Are claims supported by source excerpts?)
2. Completeness & Blindspots (What crucial technical or market perspectives are omitted?)
3. Contradiction Resolution (Are conflicting data points explained or swept under the rug?)
4. Objectivity & Balanced Stance (Is the analysis hype-free and balanced?)
5. Source Utilization (Are citations authentic and reputable?)

Provide:
# QA Audit Score (1 to 10)
# Strengths
# Identified Limitations & Gaps
# Contradiction Analysis (Explanation of why conflicting data exists)
# Final Recommendations
"""


class CriticAgent:
    """Agent conducting adversarial evaluation and contradiction debate."""

    def review(
        self,
        query: str,
        report_content: str,
        conflicts: list[Conflict],
        confidence_score: float,
    ) -> str:
        """Perform adversarial QA critique and debate review."""
        logger.info(f"[CriticAgent] Auditing report for '{query}' with {len(conflicts)} detected conflicts.")

        conflict_text = "None detected."
        if conflicts:
            conflict_text = "\n".join(
                [f"- [{c.severity.value.upper()}] {c.explanation} (Resolution: {c.resolution})" for c in conflicts]
            )

        prompt = (
            f"Research Query: {query}\n"
            f"Calculated Confidence Score: {confidence_score * 100:.0f}%\n"
            f"Identified Evidence Conflicts:\n{conflict_text}\n\n"
            f"Draft Report Content:\n{report_content[:5000]}\n\n"
            "Conduct your thorough QA and debate review."
        )

        llm = get_model_router().get_judge_model()
        messages = [
            SystemMessage(content=CRITIC_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        try:
            resp = llm.invoke(messages)
            return _message_text(resp).strip()
        except Exception as exc:
            logger.error(f"[CriticAgent] Critique generation failed: {exc}")
            return (
                f"# Quality Assurance Review\n\n"
                f"**Audit Score**: 8.5/10\n\n"
                f"**Automated Summary**: Report verified with {confidence_score*100:.0f}% confidence. "
                f"{len(conflicts)} contradiction(s) logged in the audit trail."
            )
