"""
Researcher Agent.
Executes search tasks in the dynamic plan, gathers authoritative web sources,
and applies initial quality scoring.
"""

from cognisynth.logging_config import logger
from cognisynth.schemas.research import ResearchTask, TaskStatus
from cognisynth.schemas.evidence import Source, Document
from cognisynth.tools.search import search_web_structured
from cognisynth.evidence.scorer import score_source


class ResearcherAgent:
    """Agent executing focused web search tasks."""

    def execute_task(self, task: ResearchTask, max_results: int = 3) -> tuple[list[Source], list[Document]]:
        """Execute a single search task and score returned sources."""
        task.status = TaskStatus.RUNNING
        logger.info(f"[ResearcherAgent] Executing task '{task.task_id}': {task.objective}")

        try:
            sources, documents = search_web_structured(
                query=task.objective,
                max_results=max_results,
                scrape_pages=True,
            )

            # Score each source with its extracted document
            doc_map = {d.source_id: d for d in documents}
            for src in sources:
                doc = doc_map.get(src.source_id)
                if doc:
                    score_source(src, doc)

            task.status = TaskStatus.COMPLETED
            task.output_refs = [s.source_id for s in sources]
            return sources, documents

        except Exception as exc:
            logger.error(f"[ResearcherAgent] Task '{task.task_id}' failed: {exc}")
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            return [], []
