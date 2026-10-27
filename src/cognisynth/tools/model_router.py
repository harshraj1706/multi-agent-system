"""
Multi-Model Router Architecture.
Directs specialized agent tasks to optimal model tiers:
- Qwen 3.6 (Groq): Fast tasks (planning, claim extraction)
- Compound (Groq): Research query expansion & search synthesis
- GPT-OSS 120B (Groq): Deep reasoning, claim audit & contradiction detection
- Gemini Flash: Final Judge & Publication Report Synthesis (with auto-fallback to GPT-OSS 120B)
"""

from functools import lru_cache
from typing import Optional
from langchain_core.runnables import Runnable

from cognisynth.config import settings
from cognisynth.logging_config import logger
from cognisynth.tools.llm import GeminiChatModel, get_default_llm
from cognisynth.tools.groq_adapter import GroqChatModel


class ModelRouter:
    """Central intelligent model router."""

    def __init__(self):
        self.groq_key = settings.groq_api_key
        self.gemini_key = settings.gemini_api_key

    def get_fast_model(self) -> Runnable:
        """Fast tasks: Task decomposition, planning, and claim extraction."""
        if self.groq_key:
            return GroqChatModel(model=settings.model_fast, temperature=0.1)
        return get_default_llm()

    def get_research_model(self) -> Runnable:
        """Research tasks: Query expansion and content ingestion."""
        if self.groq_key:
            return GroqChatModel(model=settings.model_research, temperature=0.2)
        return get_default_llm()

    def get_reasoning_model(self) -> Runnable:
        """Deep reasoning: Contradiction detection, claim cross-referencing."""
        if self.groq_key:
            return GroqChatModel(model=settings.model_reasoning, temperature=0.2)
        return get_default_llm()

    def get_judge_model(self) -> Runnable:
        """Final Judge & Master Synthesis: Publication report and critique."""
        # Attempts Gemini primary with automatic fallback to GPT-OSS 120B if quota exhausted
        return ResilientJudgeModel(primary_gemini=get_default_llm(), fallback_groq=self.get_reasoning_model())


class ResilientJudgeModel(Runnable):
    """Executes Gemini as Final Judge; if 429 quota or 503 persists, seamlessly falls back to GPT-OSS 120B."""

    def __init__(self, primary_gemini: Runnable, fallback_groq: Runnable):
        self.primary_gemini = primary_gemini
        self.fallback_groq = fallback_groq

    def invoke(self, input_value, config=None, **kwargs):
        try:
            return self.primary_gemini.invoke(input_value, config=config, **kwargs)
        except Exception as exc:
            logger.warning(
                f"[ModelRouter] Gemini judge quota/demand limit encountered ({exc}). "
                "Routing Final Judge to GPT-OSS 120B (Groq)..."
            )
            return self.fallback_groq.invoke(input_value, config=config, **kwargs)


@lru_cache(maxsize=1)
def get_model_router() -> ModelRouter:
    """Singleton getter for the ModelRouter."""
    return ModelRouter()
