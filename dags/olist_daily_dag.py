"""
Bonus: Airflow DAG that runs the same pipeline every day.

Copy (or symlink) this file into your Airflow dags/ folder and set OLIST_PROJECT_ROOT
to the repo path if the repo is not next to the dags folder.

Each pipeline step is its own task, so if the data-quality gate raises an alarm the
mart task never runs and Airflow marks the run as failed (you get the usual email/Slack
alert you have configured for failed tasks).
"""
import os
import sys
from datetime import datetime, timedelta

from airflow import DAG

try:  # Airflow 3.x
    from airflow.providers.standard.operators.python import PythonOperator
except ImportError:  # Airflow 2.x
    from airflow.operators.python import PythonOperator

PROJECT_ROOT = os.environ.get(
    "OLIST_PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipeline.run_pipeline import step_dq_staging, step_load, step_mart, step_staging  # noqa: E402

default_args = {
    "owner": "data-eng",
    "retries": 1,                       # one retry for flaky I/O; DQ alarms will fail again, which is what we want
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,          # switch on once SMTP is configured
}

with DAG(
    dag_id="olist_weekly_metrics_pipeline",
    description="Olist ELT: raw -> staging -> DQ gate -> mart",
    default_args=default_args,
    start_date=datetime(2026, 10, 1),
    schedule="@daily",                  # Airflow 2.4+; use schedule_interval on older versions
    catchup=False,
    max_active_runs=1,                  # two runs writing the same SQLite file at once would collide
    tags=["olist", "elt", "big-data-course"],
) as dag:

    load_raw = PythonOperator(task_id="validate_and_load_raw", python_callable=step_load)
    build_staging = PythonOperator(task_id="build_staging", python_callable=step_staging)
    dq_gate = PythonOperator(task_id="data_quality_gate", python_callable=step_dq_staging)
    build_mart = PythonOperator(task_id="build_mart_and_grain_check", python_callable=step_mart)

    load_raw >> build_staging >> dq_gate >> build_mart
