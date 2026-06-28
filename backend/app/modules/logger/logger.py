import logging
import sys
from typing import Optional


class PrettyFormatter(logging.Formatter):
    """
    Beautiful colored formatter for terminal viewing.
    Perfect for `tail -f` with emojis, aligned columns and ANSI colors.
    """

    # Level styles: emoji + color + bold
    LEVEL_STYLES = {
        "DEBUG":    ("\033[36m", "🐛"),   # cyan
        "INFO":     ("\033[32m", "✨"),   # green
        "WARNING":  ("\033[33m", "⚠️ "),  # yellow
        "ERROR":    ("\033[31m", "❌"),   # red
        "CRITICAL": ("\033[35m", "💀"),   # magenta
    }
    RESET = "\033[0m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        # Timestamp: HH:MM:SS only (cleaner for tail -f)
        timestamp = self.formatTime(record, "%H:%M:%S")

        # Level styling
        level_name = record.levelname
        color, emoji = self.LEVEL_STYLES.get(level_name, (self.WHITE, "📝"))

        # Module name: truncate and pad for alignment
        module_name = record.name
        if len(module_name) > 22:
            module_name = module_name[:19] + "…"
        module_padded = f"{module_name:22}"

        # Message: highlight HTTP status codes and URLs
        message = record.getMessage()
        message = self._highlight_message(message)

        # Build pretty line
        parts = [
            f"{self.GRAY}{timestamp}{self.RESET}",
            f"{color}{self.BOLD}{emoji}{self.RESET} {color}{level_name:8}{self.RESET}",
            f"{self.DIM}{module_padded}{self.RESET}",
            f"{message}",
        ]

        return " │ ".join(parts)

    def _highlight_message(self, msg: str) -> str:
        """Highlight common patterns in log messages."""
        # Highlight HTTP codes (200, 201, 400, 404, 500, etc)
        import re
        msg = re.sub(
            r'\b(2\d{2})\b',
            f'{self.GRAY}\033[42m\\1{self.RESET}',
            msg
        )
        msg = re.sub(
            r'\b(3\d{2})\b',
            f'{self.GRAY}\033[43m\\1{self.RESET}',
            msg
        )
        msg = re.sub(
            r'\b(4\d{2})\b',
            f'{self.GRAY}\033[41m\\1{self.RESET}',
            msg
        )
        msg = re.sub(
            r'\b(5\d{2})\b',
            f'{self.BOLD}\033[41m\\1{self.RESET}',
            msg
        )
        # Highlight URLs
        msg = re.sub(
            r'(https?://[^\s]+)',
            f'\033[34m\\1{self.RESET}',
            msg
        )
        # Highlight chat IDs / phone numbers
        msg = re.sub(
            r'(chat\s+\d+|phone\s+[^\s]+)',
            f'\033[36m\\1{self.RESET}',
            msg,
            flags=re.IGNORECASE
        )
        return msg



def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance with pretty terminal output."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = PrettyFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if level:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    return logger
