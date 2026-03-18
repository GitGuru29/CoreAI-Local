import logging

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
