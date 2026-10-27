"""
Run and Task Execution Tracer.
Records granular execution traces, timing spans, and agent state transitions.
"""

import time
from datetime import datetime, timezone
from typing import Any, Optional


class ExecutionSpan:
    """A timed operation span representing an agent action or tool invocation."""

    def __init__(self, span_id: str, name: str, agent: str, metadata: Optional[dict[str, Any]] = None):
        self.span_id = span_id
        self.name = name
        self.agent = agent
        self.metadata = metadata or {}
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.duration: float = 0.0
        self.status = "running"
        self.error: Optional[str] = None

    def finish(self, status: str = "completed", error: Optional[str] = None) -> None:
        self.end_time = time.time()
        self.duration = round(self.end_time - self.start_time, 3)
        self.status = status
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "span_id": self.span_id,
            "name": self.name,
            "agent": self.agent,
            "duration_seconds": self.duration,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
        }


class RunTracer:
    """Manages telemetry traces for an individual research run."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.spans: list[ExecutionSpan] = []
        self._active_spans: dict[str, ExecutionSpan] = {}
        self.state_transitions: list[dict[str, Any]] = []

    def start_span(self, name: str, agent: str, metadata: Optional[dict[str, Any]] = None) -> ExecutionSpan:
        import uuid
        sid = f"span_{uuid.uuid4().hex[:6]}"
        span = ExecutionSpan(sid, name, agent, metadata)
        self.spans.append(span)
        self._active_spans[sid] = span
        return span

    def finish_span(self, span: ExecutionSpan, status: str = "completed", error: Optional[str] = None) -> None:
        span.finish(status=status, error=error)
        self._active_spans.pop(span.span_id, None)

    def record_transition(self, agent: str, from_state: str, to_state: str) -> None:
        self.state_transitions.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "from_state": from_state,
            "to_state": to_state,
        })

    def total_latency(self) -> float:
        return round(sum(s.duration for s in self.spans), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "total_latency_seconds": self.total_latency(),
            "spans": [s.to_dict() for s in self.spans],
            "state_transitions": self.state_transitions,
        }
