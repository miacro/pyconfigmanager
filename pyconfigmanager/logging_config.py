import logging
import sys


def logger_config(
        logger=None,
        name=None,
        level=logging.INFO,
        format="[%(asctime)s]:%(levelname)s:%(name)s:%(message)s",
        propagate=True,
):
    if not logger or isinstance(logger, str):
        logger = logging.getLogger(logger)
    set_logger_level(logger=logger, level=level)
    if propagate is not None:
        logger.propagate = propagate
    if isinstance(name, str):
        logger.name = name
    if format is not None:
        if not logger.handlers:
            log_handler = logging.StreamHandler(sys.stderr)
            logger.addHandler(log_handler)
        for log_handler in logger.handlers:
            log_handler.setFormatter(logging.Formatter(format, None))


def set_logger_level(logger=None, level=logging.INFO):
    if not logger:
        logger = logging.getLogger()
    elif isinstance(logger, str):
        logger = logger.getLogger(logger)
    logger.setLevel(get_logging_level(level))


def get_logging_level(level):
    if isinstance(level, int):
        logging_level = level
    else:
        logging_level = logging.getLevelName(level)
    return logging_level
