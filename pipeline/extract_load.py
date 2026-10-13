"""
Step 1 of the ELT: copy each CSV into the database as a raw_* table, untouched.

Everything is loaded as TEXT on purpose. The raw layer is a faithful copy of the file,
so if something looks wrong later we can always check it against what Olist sent.
Type casting and cleaning happen in staging (sql/staging).

Idempotency: each file is written to <table>__new first and then swapped in with a
DROP + RENAME inside one transaction. Running the loader twice gives the same row counts,
never duplicates, and a crash halfway through leaves the old table intact.
"""
import hashlib
import sqlite3
from datetime import datetime, timezone

import pandas as pd

from pipeline.config import RAW_DIR, RAW_SOURCES


class PipelineError(Exception):
    """Raised when the pipeline cannot continue (missing file, missing column, bad SQL)."""


def _md5(path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_sources(log) -> None:
    """Fail before touching the database if any file or expected column is missing."""
    problems = []
    for table, (fname, expected_cols) in RAW_SOURCES.items():
        path = RAW_DIR / fname
        if not path.exists():
            problems.append(f"missing file: {path}")
            continue
        header = pd.read_csv(path, nrows=0, encoding="utf-8-sig").columns.str.strip().tolist()
        missing = [c for c in expected_cols if c not in header]
        if missing:
            problems.append(f"{fname}: expected column(s) not found -> {missing}")
    if problems:
        for p in problems:
            log.error(p)
        raise PipelineError(
            "Source validation failed. Fix the files in data/raw/ and re-run:\n  - "
            + "\n  - ".join(problems)
        )
    log.info("Source validation passed: %d files, all expected columns present", len(RAW_SOURCES))


def load_raw(conn: sqlite3.Connection, log) -> dict:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS etl_load_audit (
               table_name TEXT, source_file TEXT, file_md5 TEXT,
               row_count INTEGER, loaded_at_utc TEXT)"""
    )
    counts = {}
    for table, (fname, _) in RAW_SOURCES.items():
        path = RAW_DIR / fname
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=True)
        df.columns = df.columns.str.strip()
        df["_source_file"] = fname

        tmp = f"{table}__new"
        conn.execute(f"DROP TABLE IF EXISTS {tmp}")
        df.to_sql(tmp, conn, index=False)

        # atomic swap: either the new table fully replaces the old one, or nothing changes
        with conn:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
            conn.execute(f"ALTER TABLE {tmp} RENAME TO {table}")
            conn.execute(
                "INSERT INTO etl_load_audit VALUES (?,?,?,?,?)",
                (table, fname, _md5(path), len(df), datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
        counts[table] = len(df)
        log.info("Loaded %-26s %9s rows  <- %s", table, f"{len(df):,}", fname)
    return counts
