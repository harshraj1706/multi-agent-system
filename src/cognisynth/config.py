"""
Configuration and environment validation for CogniSynth platform.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()


class Settings(BaseModel):
    """Platform-wide configuration settings with validation and safe defaults."""

    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent / "data")

    # LLM Settings
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "router").lower())
    llm_model: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "gemini-3.7-flash"))
    llm_fallback_model: str = Field(default_factory=lambda: os.getenv("LLM_FALLBACK_MODEL", "gemini-3.8-flash"))
    llm_temperature: float = Field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.2")))
    llm_max_tokens: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "4000")))
    llm_max_retries: int = Field(default_factory=lambda: int(os.getenv("LLM_MAX_RETRIES", "3")))
    llm_initial_backoff: float = Field(default_factory=lambda: float(os.getenv("LLM_INITIAL_BACKOFF", "2.0")))

    # Model Router Topology
    model_fast: str = Field(default="qwen/qwen3.6-27b")          # Fast tasks & extraction (Groq)
    model_reasoning: str = Field(default="openai/gpt-oss-120b")  # Deep reasoning & conflicts (Groq)
    model_research: str = Field(default="groq/compound-mini")    # Research query formulation (Groq)
    model_judge: str = Field(default="gemini-3.7-flash")         # Final Judge & Synthesis (Gemini)

    # Search & Web Scraper Settings
    tavily_api_key: str = Field(default_factory=lambda: os.getenv("TAVILY_API_KEY", ""))
    tavily_max_results: int = Field(default_factory=lambda: int(os.getenv("TAVILY_MAX_RESULTS", "4")))
    max_scraped_chars: int = Field(default_factory=lambda: int(os.getenv("MAX_SCRAPED_CHARS", "5000")))
    max_research_context_chars: int = Field(
        default_factory=lambda: int(os.getenv("MAX_RESEARCH_CONTEXT_CHARS", "30000"))
    )
    request_timeout: int = Field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "120")))

    # Safeguards & Limits
    max_tasks_per_plan: int = Field(default=8)
    max_plan_depth: int = Field(default=3)
    enable_human_approval: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_HUMAN_APPROVAL", "false").lower() == "true"
    )

    # Logging
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())

    def validate_api_keys(self, require_tavily: bool = True, require_gemini: bool = True) -> None:
        """Validate presence of external API credentials."""
        missing = []
        if require_gemini and not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        if require_tavily and not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")

        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please configure them in your .env file."
            )

    model_config = {"arbitrary_types_allowed": True}


# Global singleton settings instance
settings = Settings()
os.makedirs(settings.data_dir, exist_ok=True)
