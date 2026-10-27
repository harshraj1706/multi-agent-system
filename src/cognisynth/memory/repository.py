"""
Research Run and Report Repository.
Persists complete execution records, versioned reports, and audit trails.
Computes version diff summaries between consecutive report iterations.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

from cognisynth.config import settings
from cognisynth.logging_config import logger
from cognisynth.schemas.research import ResearchRun, ResearchPlan
from cognisynth.schemas.report import Report, ReportVersion


class ResearchRepository:
    """Persistent storage for research runs, plans, reports, and version diffs."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or (settings.data_dir / "research_repository.json")
        self.runs: dict[str, dict[str, Any]] = {}
        self.plans: dict[str, dict[str, Any]] = {}
        self.reports: dict[str, dict[str, Any]] = {}
        self.report_versions: dict[str, list[dict[str, Any]]] = {}  # run_id -> list of versions
        self.load()

    def save_run(self, run: ResearchRun) -> None:
        """Persist a research run."""
        self.runs[run.run_id] = run.model_dump(mode="json")
        self.persist()

    def get_run(self, run_id: str) -> Optional[dict[str, Any]]:
        """Fetch a research run by ID."""
        return self.runs.get(run_id)

    def list_runs(self) -> list[dict[str, Any]]:
        """List all research runs, newest first."""
        return sorted(self.runs.values(), key=lambda r: r.get("created_at", ""), reverse=True)

    def save_plan(self, plan: ResearchPlan) -> None:
        """Persist a research plan."""
        self.plans[plan.plan_id] = plan.model_dump(mode="json")
        self.persist()

    def get_plan(self, plan_id: str) -> Optional[dict[str, Any]]:
        return self.plans.get(plan_id)

    def save_report(self, report: Report, claims_list: Optional[list[str]] = None, citations_list: Optional[list[str]] = None) -> ReportVersion:
        """
        Save a report and automatically create a versioned snapshot with change delta.
        """
        self.reports[report.report_id] = report.model_dump(mode="json")

        run_id = report.run_id
        past_versions = self.report_versions.get(run_id, [])
        new_version_num = len(past_versions) + 1

        claims = claims_list or []
        citations = citations_list or []

        # Calculate change delta if previous version exists
        change_summary = None
        if past_versions:
            prev = past_versions[-1]
            prev_claims = set(prev.get("claims", []))
            curr_claims = set(claims)

            new_claims = list(curr_claims - prev_claims)
            removed_claims = list(prev_claims - curr_claims)
            prev_conf = prev.get("confidence", 0.8)
            conf_delta = report.confidence_score - prev_conf

            change_summary = (
                f"Version {new_version_num} updates: "
                f"+{len(new_claims)} new claims, -{len(removed_claims)} revised claims. "
                f"Confidence delta: {conf_delta:+.2f} ({prev_conf:.2f} -> {report.confidence_score:.2f})."
            )
        else:
            change_summary = f"Initial publication (v1) with {len(claims)} claims and {len(citations)} citations."

        version_record = ReportVersion(
            report_id=report.report_id,
            version=new_version_num,
            title=report.title,
            markdown_content=report.content,
            claims=claims,
            citations=citations,
            confidence=report.confidence_score,
            change_summary=change_summary,
        )

        if run_id not in self.report_versions:
            self.report_versions[run_id] = []
        self.report_versions[run_id].append(version_record.model_dump(mode="json"))

        self.persist()
        return version_record

    def get_report_versions(self, run_id: str) -> list[dict[str, Any]]:
        """Retrieve all report versions for a run."""
        return self.report_versions.get(run_id, [])

    def persist(self) -> None:
        """Save repository state to disk."""
        try:
            os.makedirs(self.storage_path.parent, exist_ok=True)
            payload = {
                "runs": self.runs,
                "plans": self.plans,
                "reports": self.reports,
                "report_versions": self.report_versions,
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as exc:
            logger.warning(f"Failed to persist research repository: {exc}")

    def load(self) -> None:
        """Load repository state from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.runs = data.get("runs", {})
                self.plans = data.get("plans", {})
                self.reports = data.get("reports", {})
                self.report_versions = data.get("report_versions", {})
            except Exception as exc:
                logger.warning(f"Could not load repository from {self.storage_path}: {exc}")


_repo_instance: Optional[ResearchRepository] = None


def get_repository() -> ResearchRepository:
    """Singleton getter for the persistent repository."""
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = ResearchRepository()
    return _repo_instance
