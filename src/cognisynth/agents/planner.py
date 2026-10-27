"""
Dynamic Research Planner Agent.
Decomposes user research queries into directed acyclic task graphs (ResearchPlan)
with parallel search tracks, dependency tracking, and safety bounds.
"""

import json
import re
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

from cognisynth.config import settings
from cognisynth.logging_config import logger
from cognisynth.schemas.research import ResearchPlan, ResearchTask, TaskType, TaskStatus
from cognisynth.tools.llm import _message_text
from cognisynth.tools.model_router import get_model_router


PLANNER_SYSTEM_PROMPT = """You are the Lead Planning Agent for CogniSynth, an autonomous decision intelligence platform.
Your job is to break down a research objective into a structured, dependency-aware task graph.

Decompose the topic into:
1. 2 to 3 parallel search/discovery tasks investigating distinct angles (e.g., technical mechanisms, real-world benchmarks, limitations/controversies).
2. 1 synthesis task that aggregates the research findings.
3. 1 verification & quality critique task.

Respond ONLY with a valid JSON array of tasks with this structure:
[
  {
    "task_id": "task_1",
    "type": "search",
    "objective": "Detailed search query and focus area",
    "dependencies": [],
    "priority": 1
  },
  {
    "task_id": "task_2",
    "type": "search",
    "objective": "Second complementary focus area",
    "dependencies": [],
    "priority": 1
  },
  {
    "task_id": "task_synth",
    "type": "synthesize",
    "objective": "Synthesize verified findings across all sources",
    "dependencies": ["task_1", "task_2"],
    "priority": 2
  },
  {
    "task_id": "task_review",
    "type": "critique",
    "objective": "Adversarial QA and contradiction verification",
    "dependencies": ["task_synth"],
    "priority": 3
  }
]
"""


class PlannerAgent:
    """Agent that generates bounded, dynamic ResearchPlans."""

    def __init__(self, max_tasks: Optional[int] = None, max_depth: Optional[int] = None):
        self.max_tasks = max_tasks or settings.max_tasks_per_plan
        self.max_depth = max_depth or settings.max_plan_depth

    def _generate_default_plan(self, objective: str) -> ResearchPlan:
        """Deterministic heuristic fallback plan ensuring zero pipeline failures."""
        task1 = ResearchTask(
            task_id="task_search_tech",
            type=TaskType.SEARCH,
            objective=f"Core architecture, state-of-the-art methodology, and developments in {objective}",
            dependencies=[],
            priority=1,
        )
        task2 = ResearchTask(
            task_id="task_search_impact",
            type=TaskType.SEARCH,
            objective=f"Real-world performance, challenges, benchmarks, and limitations of {objective}",
            dependencies=[],
            priority=1,
        )
        task_synth = ResearchTask(
            task_id="task_synthesis",
            type=TaskType.SYNTHESIZE,
            objective=f"Synthesize comprehensive evidence-grounded report on {objective}",
            dependencies=[task1.task_id, task2.task_id],
            priority=2,
        )
        task_critique = ResearchTask(
            task_id="task_critique",
            type=TaskType.CRITIQUE,
            objective=f"Audit claims, detect contradictions, and score confidence for {objective}",
            dependencies=[task_synth.task_id],
            priority=3,
        )
        return ResearchPlan(
            objective=objective,
            tasks=[task1, task2, task_synth, task_critique],
            constraints={"max_tasks": self.max_tasks, "heuristic_fallback": True},
        )

    def plan(self, objective: str) -> ResearchPlan:
        """
        Generate a dynamic research plan using LLM with deterministic fallback safeguards.
        """
        objective = objective.strip()
        if not objective:
            raise ValueError("Research objective cannot be empty.")

        try:
            llm = get_model_router().get_fast_model()
            messages = [
                SystemMessage(content=PLANNER_SYSTEM_PROMPT),
                HumanMessage(content=f"Research Objective: {objective}"),
            ]
            response = llm.invoke(messages)
            text = _message_text(response).strip()

            # Clean JSON formatting block if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            if not isinstance(data, list) or not data:
                return self._generate_default_plan(objective)

            tasks: list[ResearchTask] = []
            seen_ids = set()

            for item in data[: self.max_tasks]:
                tid = str(item.get("task_id", f"task_{len(tasks)+1}"))
                if tid in seen_ids:
                    tid = f"{tid}_{len(tasks)}"
                seen_ids.add(tid)

                raw_type = str(item.get("type", "search")).lower()
                try:
                    task_type = TaskType(raw_type)
                except ValueError:
                    task_type = TaskType.SEARCH

                deps = [d for d in item.get("dependencies", []) if d in seen_ids or d != tid]

                task = ResearchTask(
                    task_id=tid,
                    type=task_type,
                    objective=str(item.get("objective") or f"Research subtask for {objective}"),
                    dependencies=deps,
                    priority=int(item.get("priority", 1)),
                )
                tasks.append(task)

            if len(tasks) < 2:
                return self._generate_default_plan(objective)

            return ResearchPlan(
                objective=objective,
                tasks=tasks,
                constraints={"max_tasks": self.max_tasks, "llm_generated": True},
            )

        except Exception as exc:
            logger.info(f"Planner LLM generated fallback plan ({exc}). Using structured template.")
            return self._generate_default_plan(objective)
