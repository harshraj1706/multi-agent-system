"""
Structured logging configuration for CogniSynth with correlation and run IDs.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines with run_id and metadata."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "run_id") and record.run_id:
            log_obj["run_id"] = record.run_id
        if hasattr(record, "task_id") and record.task_id:
            log_obj["task_id"] = record.task_id
        if hasattr(record, "agent") and record.agent:
            log_obj["agent"] = record.agent
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logger(name: str = "cognisynth", level: str = "INFO") -> logging.Logger:
    """Setup and return a structured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", "%Y-%m-%d %H:%M:%S")
        )
        logger.addHandler(handler)

    return logger


logger = setup_logger()
