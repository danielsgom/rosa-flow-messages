import logging
import sys

from app.modules.logger import PrettyFormatter


def setup_logging(level: str = "INFO"):
    """Configure root logger with pretty colored output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    formatter = PrettyFormatter()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
