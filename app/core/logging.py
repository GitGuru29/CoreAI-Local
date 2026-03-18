import logging

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_LOGGING_CONFIGURED = False


def setup_logging(level: str) -> None:
    global _LOGGING_CONFIGURED

    resolved_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()

    if not _LOGGING_CONFIGURED:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        _LOGGING_CONFIGURED = True

    root_logger.setLevel(resolved_level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
