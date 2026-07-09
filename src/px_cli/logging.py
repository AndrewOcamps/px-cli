import logging
import sys

_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("px")
    logger.setLevel(logging.WARNING)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    logger.addHandler(handler)

    _logger = logger
    return logger


def set_verbose(verbose: bool = True) -> None:
    get_logger().setLevel(logging.DEBUG if verbose else logging.WARNING)
