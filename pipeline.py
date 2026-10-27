"""
CogniSynth Research Pipeline Entry Point.
Provides full backward compatibility with the legacy pipeline interface
while dispatching to the upgraded multi-agent architecture and structured SSE events.
"""

import os
import sys
from pathlib import Path
from typing import Generator

# Ensure src/ is on python path
src_path = str(Path(__file__).resolve().parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cognisynth.services.research_service import get_research_service
from cognisynth.config import settings

MAX_RESEARCH_CONTEXT_CHARS = settings.max_research_context_chars


def _limit_text(text: str, max_chars: int = MAX_RESEARCH_CONTEXT_CHARS) -> str:
    """Keep context bounded without removing the strongest early source material."""
    if len(text) <= max_chars:
        return text
    trimmed = text[:max_chars].rsplit("\n", 1)[0]
    return f"{trimmed}\n\n[Context trimmed to reduce token usage.]"


def run_research_pipeline_stream(topic: str) -> Generator[str, None, None]:
    """
    Stream research events for a given topic.
    Delegates to the modular CogniSynth master research service.
    """
    service = get_research_service()
    yield from service.run_research_stream(topic=topic, max_sources=settings.tavily_max_results)


def run_research_pipeline(topic: str) -> dict:
    """
    Synchronous research execution for CLI and automated scripts.
    """
    import json
    report = ""
    for event_str in run_research_pipeline_stream(topic):
        try:
            data = json.loads(event_str)
            if data.get("type") == "complete":
                report = data.get("report", "")
        except Exception:
            pass
    return {"topic": topic, "report": report}


if __name__ == "__main__":
    try:
        user_topic = input("\nEnter a research topic: ").strip()
        result = run_research_pipeline(user_topic)
        print("\n" + "=" * 60)
        print(result["report"])
        print("=" * 60)
    except Exception as exc:
        print(f"\nPipeline failed: {exc}")
        raise
