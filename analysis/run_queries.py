"""
Runs every sql/analysis/*.sql file against data/olist.db and writes the result to
reports/query_results/<name>.csv. All the logic lives in the SQL; Python only executes
the file and saves the rows (no pandas here, on purpose).

    python -m analysis.run_queries
"""
import csv
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "olist.db"
SQL = ROOT / "sql" / "analysis"
OUT = ROOT / "reports" / "query_results"


def main() -> int:
    if not DB.exists():
        print(f"Database not found at {DB}. Run `python -m pipeline.run_pipeline` first.")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    for path in sorted(SQL.glob("*.sql")):
        cur = conn.execute(path.read_text())
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        with open(OUT / f"{path.stem}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        print(f"{path.name:<36} -> {len(rows):>4} rows  ({OUT.name}/{path.stem}.csv)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
