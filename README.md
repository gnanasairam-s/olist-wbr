# Olist Weekly Business Review – ELT pipeline + analysis

Take-home assignment 1, Big Data in Industry.
Sattar Gnana Sai Ram · Roll No 48 · Reg No 127003233 · Section D

A small ELT pipeline that loads the Olist Brazilian e-commerce dataset into SQLite
(raw → staging → mart), stops with an alarm if data-quality checks fail, and then
answers the business questions with plain SQL (CTEs + window functions).

## Folder layout

```
olist-wbr/
├── data/raw/                 <- put the 9 Olist CSVs here (not committed)
├── pipeline/
│   ├── config.py             expected files + columns, paths
│   ├── extract_load.py       CSV -> raw_* tables (validation, atomic swap)
│   ├── quality.py            runs sql/checks, raises DataQualityAlarm
│   ├── logger.py             console + logs/pipeline_<timestamp>.log
│   └── run_pipeline.py       entry point
├── sql/
│   ├── staging/              stg_*.sql  (typing, dedup, fixes)
│   ├── mart/mart_orders.sql  1 row per order + mart_order_items
│   ├── checks/               Part B: 00_raw_profile + 8 checks
│   ├── analysis/             Part C: q1 ... q5
│   └── metrics/weekly_kpis.sql   Part D: North Star + guardrails per week
├── analysis/
│   ├── run_queries.py        runs sql/analysis/*.sql -> reports/query_results/*.csv
│   └── make_charts.py        4 report charts -> reports/figures/
├── dags/olist_daily_dag.py   bonus Airflow DAG (@daily)
└── requirements.txt
```

## How to run (step by step)

Tested with Python 3.13 on Linux. Windows/macOS work the same, just use `python` instead of `python3` if that's your setup.

1. **Clone and create a virtual env**
   ```bash
   git clone <this repo>
   cd olist-wbr
   python3 -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Get the data.** Download the dataset from
   https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce, unzip it, and copy all
   9 CSV files into `data/raw/`. (Olist also publishes the same files at
   https://github.com/olist/work-at-olist-data/tree/master/datasets.)
   ```
   data/raw/olist_orders_dataset.csv
   data/raw/olist_order_items_dataset.csv
   data/raw/olist_order_payments_dataset.csv
   data/raw/olist_order_reviews_dataset.csv
   data/raw/olist_customers_dataset.csv
   data/raw/olist_sellers_dataset.csv
   data/raw/olist_products_dataset.csv
   data/raw/olist_geolocation_dataset.csv
   data/raw/product_category_name_translation.csv
   ```

3. **Run the pipeline** (about 15 seconds):
   ```bash
   python3 -m pipeline.run_pipeline
   ```
   This creates `data/olist.db`. Exit code `0` = success, `1` = missing file/column or
   SQL error, `2` = data-quality alarm. Every run also writes a log to `logs/`.

4. **Run the Part C queries** (results go to `reports/query_results/`):
   ```bash
   python3 -m analysis.run_queries
   ```

5. **Make the charts** (`reports/figures/`):
   ```bash
   python3 -m analysis.make_charts
   ```

You can run step 3 as many times as you like. Each raw table is rebuilt in a
`<table>__new` copy and swapped in inside one transaction, and every staging/mart
file starts with `DROP TABLE IF EXISTS`, so row counts stay identical between runs
(99,441 orders in `mart_orders` every time).

## Things you can try to see the failure handling

| What to do | What happens |
|---|---|
| Move `olist_order_payments_dataset.csv` out of `data/raw/` | `PIPELINE FAILED ... missing file: .../olist_order_payments_dataset.csv`, exit 1, DB untouched |
| Delete the `order_estimated_delivery_date` column from the orders CSV | `expected column(s) not found -> ['order_estimated_delivery_date']`, exit 1 |
| Set one `order_delivered_customer_date` to `2010-01-01` | `DQ FAIL 02_delivered_before_purchase ... DATA QUALITY ALARM`, exit 2, mart not rebuilt |

## Airflow (bonus)

```bash
pip install "apache-airflow>=2.7"           # or follow the official constraints-file install
export AIRFLOW_HOME=~/airflow
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/dags
airflow db migrate
airflow dags test olist_weekly_metrics_pipeline 2026-10-12   # one full run
airflow standalone                                           # UI + scheduler, runs @daily
```

The DAG has four tasks: `validate_and_load_raw >> build_staging >> data_quality_gate >> build_mart_and_grain_check`.
A failed check fails the `data_quality_gate` task, so the mart is never refreshed with bad data.
Tested with Airflow 3.1.8 (`airflow dags test` finished with state=success); the import
falls back to the Airflow 2 path automatically.

## Key definitions used everywhere

- **Revenue / GMV** = `SUM(price + freight_value)` from order items, for orders that are not
  `canceled`/`unavailable`. Payments are not used for revenue because they include
  credit-card installment interest.
- **Customer** = `customer_unique_id`. `customer_id` is re-issued on every order, so using it
  gives a 0% repeat rate.
- **Late** = delivered date (day) > estimated delivery date (day).
