import logging
import sys
from datetime import datetime

from pipeline.config import LOG_DIR


def get_logger(name: str = "olist_pipeline") -> logging.Logger:
    """Logs to the console and to logs/pipeline_<timestamp>.log at the same time."""
    logger = logging.getLogger(name)
    if logger.handlers:  # already set up (e.g. called twice inside Airflow)
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    run_file = LOG_DIR / f"pipeline_{datetime.now():%Y%m%d_%H%M%S}.log"
    fh = logging.FileHandler(run_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger
