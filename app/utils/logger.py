import logging
import os

def get_logger(name: str) -> logging.Logger:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        ch = logging.StreamHandler()
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    return logger
