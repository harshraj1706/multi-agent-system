"""
Pydantic schemas for research requests, plans, tasks, and execution runs.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    SEARCH = "search"
    SCRAPE = "scrape"
    EXTRACT_CLAIMS = "extract_claims"
    VERIFY = "verify"
    SYNTHESIZE = "synthesize"
    CRITIQUE = "critique"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RunStatus(str, Enum):
    QUEUED = "queued"
    PLANNING = "planning"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchTask(BaseModel):
    """An individual research task in the dynamic execution graph."""

    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    type: TaskType = Field(default=TaskType.SEARCH)
    objective: str
    dependencies: list[str] = Field(default_factory=list)
    priority: int = Field(default=1)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    output_refs: list[str] = Field(default_factory=list)
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class ResearchPlan(BaseModel):
    """Dynamic plan decomposing a research query into a task graph."""

    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    objective: str
    tasks: list[ResearchTask] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_task(self, task_id: str) -> Optional[ResearchTask]:
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    def ready_tasks(self) -> list[ResearchTask]:
        """Return tasks whose dependencies are completed and status is pending."""
        completed_ids = {t.task_id for t in self.tasks if t.status == TaskStatus.COMPLETED}
        return [
            t
            for t in self.tasks
            if t.status == TaskStatus.PENDING and set(t.dependencies).issubset(completed_ids)
        ]


class ResearchRequest(BaseModel):
    """Incoming user research request."""

    query: str
    max_sources: int = 4
    depth: str = "standard"  # standard, deep, rapid
    require_approval: bool = False
    domain_filter: list[str] = Field(default_factory=list)


class ResearchRun(BaseModel):
    """Audit and state record for a complete research execution."""

    run_id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:10]}")
    query: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: RunStatus = Field(default=RunStatus.QUEUED)
    plan_id: Optional[str] = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    final_report_id: Optional[str] = None
    error: Optional[str] = None
