"""
Human-in-the-loop approval service.
Manages checkpoints for plan modification, evidence review, and publication approval.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid

from cognisynth.logging_config import logger


class CheckpointType(str, Enum):
    PLAN_REVIEW = "plan_review"
    EVIDENCE_REVIEW = "evidence_review"
    FINAL_PUBLICATION = "final_publication"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class ApprovalCheckpoint:
    def __init__(
        self,
        checkpoint_id: str,
        run_id: str,
        checkpoint_type: CheckpointType,
        data: dict[str, Any],
        status: ApprovalStatus = ApprovalStatus.PENDING,
        feedback: Optional[str] = None,
    ):
        self.checkpoint_id = checkpoint_id
        self.run_id = run_id
        self.checkpoint_type = checkpoint_type
        self.data = data
        self.status = status
        self.feedback = feedback
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.resolved_at: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "run_id": self.run_id,
            "checkpoint_type": self.checkpoint_type.value,
            "data": self.data,
            "status": self.status.value,
            "feedback": self.feedback,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }


class ApprovalService:
    """Manages pause-and-resume approval gates and audit logs."""

    def __init__(self):
        self._checkpoints: dict[str, ApprovalCheckpoint] = {}  # checkpoint_id -> checkpoint
        self._run_checkpoints: dict[str, list[str]] = {}       # run_id -> list of checkpoint_ids

    def create_checkpoint(
        self,
        run_id: str,
        checkpoint_type: CheckpointType,
        data: dict[str, Any],
    ) -> ApprovalCheckpoint:
        cid = f"chk_{uuid.uuid4().hex[:8]}"
        cp = ApprovalCheckpoint(
            checkpoint_id=cid,
            run_id=run_id,
            checkpoint_type=checkpoint_type,
            data=data,
        )
        self._checkpoints[cid] = cp
        if run_id not in self._run_checkpoints:
            self._run_checkpoints[run_id] = []
        self._run_checkpoints[run_id].append(cid)
        logger.info(f"[ApprovalService] Checkpoint '{cid}' created for run '{run_id}' ({checkpoint_type.value})")
        return cp

    def resolve_checkpoint(
        self,
        checkpoint_id: str,
        status: ApprovalStatus,
        feedback: Optional[str] = None,
        modifications: Optional[dict[str, Any]] = None,
    ) -> Optional[ApprovalCheckpoint]:
        cp = self._checkpoints.get(checkpoint_id)
        if not cp:
            return None

        cp.status = status
        cp.feedback = feedback
        if modifications:
            cp.data.update(modifications)
        cp.resolved_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"[ApprovalService] Checkpoint '{checkpoint_id}' resolved: {status.value}")
        return cp

    def get_pending_checkpoint(self, run_id: str) -> Optional[ApprovalCheckpoint]:
        cids = self._run_checkpoints.get(run_id, [])
        for cid in reversed(cids):
            cp = self._checkpoints.get(cid)
            if cp and cp.status == ApprovalStatus.PENDING:
                return cp
        return None

    def get_run_audit_trail(self, run_id: str) -> list[dict[str, Any]]:
        cids = self._run_checkpoints.get(run_id, [])
        return [self._checkpoints[cid].to_dict() for cid in cids if cid in self._checkpoints]


_approval_service_instance: Optional[ApprovalService] = None


def get_approval_service() -> ApprovalService:
    global _approval_service_instance
    if _approval_service_instance is None:
        _approval_service_instance = ApprovalService()
    return _approval_service_instance
