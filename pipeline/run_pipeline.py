"""
Olist weekly-metrics ELT pipeline.

    python -m pipeline.run_pipeline

Steps
  1. validate   - every expected CSV and column is present (fails loudly otherwise)
  2. load_raw   - CSV -> raw_* tables (atomic swap, so re-runs never duplicate)
  3. profile    - count data-quality issues on raw data (for the report)
  4. staging    - sql/staging/*.sql  -> stg_* tables (typed, deduped, fixed)
  5. dq_gate    - sql/checks/01-07   -> alarm and stop if any check is out of tolerance
  6. mart       - sql/mart/*.sql     -> mart_orders (1 row per order), mart_order_items
  7. dq_gate    - sql/checks/08      -> mart grain check

Every staging/mart file starts with DROP TABLE IF EXISTS, and each file runs in its own
transaction, so the whole pipeline is safe to run as many times as you like.
"""
import sqlite3
import sys
import time

from pipeline.config import DB_PATH, MART_SQL, SQL_DIR, STAGING_SQL
from pipeline.extract_load import PipelineError, load_raw, validate_sources
from pipeline.logger import get_logger
from pipeline.quality import DataQualityAlarm, profile_raw, run_checks


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def run_sql_files(conn, folder: str, files: list, log) -> None:
    for fname in files:
        path = SQL_DIR / folder / fname
        if not path.exists():
            raise PipelineError(f"SQL file not found: {path}")
        t0 = time.time()
        try:
            # one transaction per file: if a statement fails, the old table survives
            conn.executescript("BEGIN;\n" + path.read_text() + "\nCOMMIT;")
        except sqlite3.Error as e:
            conn.rollback()
            raise PipelineError(f"{folder}/{fname} failed: {e}") from e
        table = fname.replace(".sql", "")
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        log.info("Built %-22s %9s rows  (%.1fs)", table, f"{n:,}", time.time() - t0)


# small wrappers so Airflow can call each step as its own task
def step_load(log=None):
    log = log or get_logger()
    validate_sources(log)
    with connect() as conn:
        load_raw(conn, log)
        profile_raw(conn, log)


def step_staging(log=None):
    log = log or get_logger()
    with connect() as conn:
        run_sql_files(conn, "staging", STAGING_SQL, log)


def step_dq_staging(log=None):
    log = log or get_logger()
    with connect() as conn:
        run_checks(conn, "staging", log)


def step_mart(log=None):
    log = log or get_logger()
    with connect() as conn:
        run_sql_files(conn, "mart", MART_SQL, log)
        run_checks(conn, "mart", log)


def main() -> int:
    log = get_logger()
    log.info("=== Olist pipeline start  (db: %s) ===", DB_PATH)
    t0 = time.time()
    try:
        log.info("--- [1/4] validate + load raw ---")
        step_load(log)
        log.info("--- [2/4] staging ---")
        step_staging(log)
        log.info("--- [3/4] data-quality gate ---")
        step_dq_staging(log)
        log.info("--- [4/4] mart + grain check ---")
        step_mart(log)
    except DataQualityAlarm as e:
        log.critical("DATA QUALITY ALARM\n%s", e)
        return 2
    except PipelineError as e:
        log.critical("PIPELINE FAILED\n%s", e)
        return 1
    log.info("=== Pipeline finished OK in %.1fs ===", time.time() - t0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
