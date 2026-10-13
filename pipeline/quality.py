"""
Data-quality gate (Part B).

Every check in sql/checks/NN_*.sql returns one row: failed_rows, checked_rows.
Each check has a tolerance below. If failed_rows / checked_rows goes above it, we raise
DataQualityAlarm and the pipeline stops -- the mart is not rebuilt, so nobody downstream
reads bad numbers.

  max_fail_rate = 0      -> blocking: the issue must have been fixed/dropped in staging
  max_fail_rate > 0      -> known, flagged issue; alarm only if it suddenly grows
"""
import sqlite3
from datetime import datetime, timezone

from pipeline.config import SQL_DIR

CHECKS_DIR = SQL_DIR / "checks"

# file stem -> (stage it runs after, max allowed failure rate, how we handle it)
CHECKS = {
    "01_order_id_null_or_duplicate":      ("staging", 0.0,   "blocking - would drop/dedupe"),
    "02_delivered_before_purchase":       ("staging", 0.0,   "blocking"),
    "03_payment_vs_items_mismatch":       ("staging", 0.01,  "flagged in mart (is_payment_mismatch)"),
    "04_orders_without_customer":         ("staging", 0.0,   "blocking"),
    "05_multiple_reviews_per_order":      ("staging", 0.0,   "fixed - keep latest review"),
    "06_carrier_timestamp_out_of_window": ("staging", 0.0,   "fixed - carrier date set to NULL"),
    "07_delivered_without_delivery_date": ("staging", 0.001, "flagged, excluded from delivery KPIs"),
    "08_mart_grain_one_row_per_order":    ("mart",    0.0,   "blocking - join fan-out guard"),
}


class DataQualityAlarm(Exception):
    pass


def _ensure_results_table(conn):
    conn.execute(
        """CREATE TABLE IF NOT EXISTS dq_results (
               run_at_utc TEXT, layer TEXT, check_name TEXT,
               failed_rows INTEGER, checked_rows INTEGER,
               max_fail_rate REAL, status TEXT, handling TEXT)"""
    )


def profile_raw(conn: sqlite3.Connection, log) -> dict:
    """Count issues on the raw tables, before any cleaning. Never blocks."""
    _ensure_results_table(conn)
    sql = (CHECKS_DIR / "00_raw_profile.sql").read_text()
    run_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = {}
    with conn:
        for name, failed in conn.execute(sql).fetchall():
            results[name] = failed
            conn.execute(
                "INSERT INTO dq_results VALUES (?,?,?,?,?,?,?,?)",
                (run_at, "raw", name, failed, None, None, "INFO", CHECKS[name][2]),
            )
            log.info("RAW PROFILE  %-36s %6d rows affected", name, failed)
    return results


def run_checks(conn: sqlite3.Connection, stage: str, log) -> list:
    _ensure_results_table(conn)
    run_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    alarms, rows = [], []
    for name, (check_stage, max_rate, handling) in CHECKS.items():
        if check_stage != stage:
            continue
        path = CHECKS_DIR / f"{name}.sql"
        if not path.exists():
            raise DataQualityAlarm(f"Check file missing: {path}")
        failed, checked = conn.execute(path.read_text()).fetchone()
        failed, checked = int(failed or 0), int(checked or 0)
        rate = failed / checked if checked else 0.0
        status = "PASS" if rate <= max_rate else "FAIL"
        rows.append((run_at, stage, name, failed, checked, max_rate, status, handling))
        msg = f"DQ {status}  {name:<36} failed={failed:>5} / {checked:>6}  ({rate:.3%}, limit {max_rate:.2%})"
        (log.info if status == "PASS" else log.error)(msg)
        if status == "FAIL":
            alarms.append(msg)

    with conn:
        conn.executemany("INSERT INTO dq_results VALUES (?,?,?,?,?,?,?,?)", rows)

    if alarms:
        raise DataQualityAlarm(
            f"{len(alarms)} data-quality check(s) failed after the {stage} step. "
            "Pipeline stopped so downstream tables are not refreshed:\n  " + "\n  ".join(alarms)
        )
    return rows
