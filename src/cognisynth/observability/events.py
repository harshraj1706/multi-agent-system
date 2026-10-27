"""
Typed, versioned streaming event contracts for SSE and UI consumers.
Maintains backward compatibility with legacy {"type": "log" | "status" | "metric" | "complete" | "error"}
while adding rich structured payloads: "plan", "sources", "claims", "conflicts", "trace".
"""

import json
from typing import Any, Optional


class StreamEvent:
    """Helper to emit structured, versioned JSON events."""

    @staticmethod
    def status(agent: str, state: str, run_id: Optional[str] = None) -> str:
        payload = {"type": "status", "agent": agent, "state": state, "schema_version": "1.0"}
        if run_id:
            payload["run_id"] = run_id
        return json.dumps(payload)

    @staticmethod
    def log(message: str, agent: Optional[str] = None, run_id: Optional[str] = None) -> str:
        payload = {"type": "log", "message": message, "schema_version": "1.0"}
        if agent:
            payload["agent"] = agent
        if run_id:
            payload["run_id"] = run_id
        return json.dumps(payload)

    @staticmethod
    def plan(plan_dict: dict[str, Any], run_id: Optional[str] = None) -> str:
        return json.dumps({
            "type": "plan",
            "plan": plan_dict,
            "run_id": run_id,
            "schema_version": "1.0",
        })

    @staticmethod
    def sources(sources: list[dict[str, Any]], run_id: Optional[str] = None) -> str:
        return json.dumps({
            "type": "sources",
            "sources": sources,
            "sources_count": len(sources),
            "run_id": run_id,
            "schema_version": "1.0",
        })

    @staticmethod
    def claims(claims: list[dict[str, Any]], run_id: Optional[str] = None) -> str:
        return json.dumps({
            "type": "claims",
            "claims": claims,
            "claims_count": len(claims),
            "run_id": run_id,
            "schema_version": "1.0",
        })

    @staticmethod
    def conflicts(conflicts: list[dict[str, Any]], run_id: Optional[str] = None) -> str:
        return json.dumps({
            "type": "conflicts",
            "conflicts": conflicts,
            "conflicts_count": len(conflicts),
            "run_id": run_id,
            "schema_version": "1.0",
        })

    @staticmethod
    def metric(
        sources_count: int,
        pages_analyzed: int,
        claims_count: int = 0,
        confidence_score: float = 0.8,
        cost_usd: float = 0.0,
        latency_sec: float = 0.0,
        run_id: Optional[str] = None,
    ) -> str:
        return json.dumps({
            "type": "metric",
            "sources_count": sources_count,
            "pages_analyzed": pages_analyzed,
            "claims_count": claims_count,
            "confidence_score": round(confidence_score, 2),
            "cost_usd": cost_usd,
            "latency_seconds": latency_sec,
            "run_id": run_id,
            "schema_version": "1.0",
        })

    @staticmethod
    def trace(trace_dict: dict[str, Any]) -> str:
        return json.dumps({
            "type": "trace",
            "trace": trace_dict,
            "schema_version": "1.0",
        })

    @staticmethod
    def complete(
        report: str,
        report_id: Optional[str] = None,
        confidence_score: float = 0.8,
        run_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        return json.dumps({
            "type": "complete",
            "report": report,
            "report_id": report_id,
            "confidence_score": round(confidence_score, 2),
            "run_id": run_id,
            "metadata": metadata or {},
            "schema_version": "1.0",
        })

    @staticmethod
    def error(message: str, run_id: Optional[str] = None) -> str:
        return json.dumps({
            "type": "error",
            "message": message,
            "run_id": run_id,
            "schema_version": "1.0",
        })
