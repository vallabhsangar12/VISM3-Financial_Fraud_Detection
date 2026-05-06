# ============================================================
# Structured Logger — backend/utils/logger.py
# ============================================================

import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "reports", "logs")
os.makedirs(_LOG_DIR, exist_ok=True)


class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON for easy parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def get_logger(name: str = "fraud_system") -> logging.Logger:
    """
    Return a named logger with console + rotating file handlers.

    Args:
        name: Logger name (module name recommended)

    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)

    if logger.handlers:          # Avoid duplicate handlers on re-import
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler (human-readable)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s — %(name)s — %(message)s",
                                      datefmt="%H:%M:%S"))

    # File handler (JSON, 5 MB max, 3 backups)
    fh = RotatingFileHandler(
        os.path.join(_LOG_DIR, "system.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(JsonFormatter())

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


# Shared application logger
logger = get_logger("fraud_system")
