import sys
import logging
import json

class MCPJsonFormatter(logging.Formatter):
    def format(self, record):
        log_payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "GLOBAL"),
            "session_id": getattr(record, "session_id", "INITIAL"),
            "transport": getattr(record, "transport", "stdio"),
            "tool": getattr(record, "tool", "NONE"),
            "duration_ms": getattr(record, "duration_ms", None),
            "error": getattr(record, "error", None)
        }
        return json.dumps(log_payload)

def setup_mcp_logger():
    logger = logging.getLogger("MCPServerCore")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(MCPJsonFormatter())
        logger.addHandler(stderr_handler)
    return logger

mcp_logger = setup_mcp_logger()
