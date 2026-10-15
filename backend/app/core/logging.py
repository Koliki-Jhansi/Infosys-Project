import logging
import json
import re
from typing import Any, Dict

SENSITIVE_PATTERNS = [
    re.compile(r'(password|token|secret|authorization|api[-_]?key)["\']?\s*[:=]\s*["\']?([^"\'\s,]+)', re.IGNORECASE)
]

def redact_sensitive(text: str) -> str:
    redacted = text
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub(r'\1: [REDACTED]', redacted)
    return redacted

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_sensitive(record.getMessage()),
        }
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id
        if hasattr(record, "ticket_id"):
            log_obj["ticket_id"] = record.ticket_id
        if hasattr(record, "workflow_id"):
            log_obj["workflow_id"] = record.workflow_id
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logger(name: str = "aero_assistant") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
    return logger

logger = setup_logger()
