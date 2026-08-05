import os
import logging
from datetime import datetime
import structlog
from healthPilot.core.config import get_settings


class CustomLogger:
    def __init__(self, log_dir="logs"):
        # Ensure logs directory exists
        self.logs_dir = os.path.join(os.getcwd(), log_dir)
        os.makedirs(self.logs_dir, exist_ok=True)

        # Timestamped log file (for persistence)
        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        self.log_file_path = os.path.join(self.logs_dir, log_file)

    def _resolve_log_level(self) -> int:
        raw = get_settings().LOG_LEVEL
        normalized = str(raw).strip().upper()

        if normalized == "WARN":
            normalized = "WARNING"
        if normalized == "FATAL":
            normalized = "CRITICAL"

        level = logging.getLevelName(normalized)
        return level if isinstance(level, int) else logging.INFO

    def get_logger(self, name=__file__):
        logger_name = os.path.basename(name)

        level = self._resolve_log_level()

        # Configure logging for console + file (both JSON)
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter("%(message)s"))  # Raw JSON lines

        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        logging.basicConfig(
            level=level,
            format="%(message)s",  # Structlog will handle JSON rendering
            handlers=[console_handler, file_handler],
        )

        # Configure structlog for JSON structured logging
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
                structlog.processors.add_log_level,
                structlog.processors.EventRenamer(to="event"),
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        return structlog.get_logger(logger_name)


# --- Usage Example ---
if __name__ == "__main__":
    logger = CustomLogger().get_logger(__file__)
    logger.info("User uploaded a file", user_id=123, filename="report.pdf")
    logger.error("Failed to process PDF", error="File not found", user_id=123)
    logger.critical("Critical error occurred", error="System崩溃", user_id=123)
