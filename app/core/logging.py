import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_LOGGING_CONFIGURED = False


def setup_logging(level: str, log_dir: str = "logs", log_file: str = "server.log") -> None:
    global _LOGGING_CONFIGURED

    resolved_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()

    if not _LOGGING_CONFIGURED:
        root_logger.handlers.clear()
        formatter = logging.Formatter(LOG_FORMAT)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path / log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        _LOGGING_CONFIGURED = True

    root_logger.setLevel(resolved_level)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
