import logging
import json
from datetime import datetime, UTC
from django.core.mail import mail_admins
import os


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "ip_address"):
            log_entry["ip_address"] = record.ip_address

        return json.dumps(log_entry)

class AdminEmailHandler(logging.Handler):
    """Send critical errors to admin email"""

    def emit(self, record):
        try:
            subject = f"[EthioNex] {record.levelname}: {record.getMessage()[:50]}"
            message = self.format(record)
            mail_admins(subject, message, fail_silently=True)
        except Exception:
            pass


def get_logger(name, log_file="app.log"):
    """Get configured logger instance"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # File handler with JSON formatting
    file_handler = logging.FileHandler(f"logs/{log_file}")
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # Console handler for development
    if os.environ.get("DEBUG", "0") == "1":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(console_handler)

    return logger
