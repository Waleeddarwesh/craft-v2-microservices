import json
import logging
from datetime import datetime

class RequestIDFilter(logging.Filter):
    """
    Adds the request_id from contextvars to the log record.
    """
    def filter(self, record):
        from craft_common.middleware.request_id import get_request_id
        record.request_id = get_request_id() or "no-request-id"
        return True

class JsonFormatter(logging.Formatter):
    """
    Formats log records as JSON.
    """
    def __init__(self, service_name="unknown"):
        super().__init__()
        self.service_name = service_name

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "request_id": getattr(record, "request_id", "no-request-id"),
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)
