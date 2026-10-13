"""
Central config for the pipeline: where things live and what we expect the raw files to look like.

If Olist ever changes a file name or drops a column, this is the one place to update,
and the loader will refuse to run until the files match what is written here.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DB_PATH = PROJECT_ROOT / "data" / "olist.db"
SQL_DIR = PROJECT_ROOT / "sql"
LOG_DIR = PROJECT_ROOT / "logs"

# raw table name -> (csv file name, columns we rely on downstream)
# We only list the columns we actually use. Extra columns in the file are fine,
# missing ones are not.
RAW_SOURCES = {
    "raw_orders": (
        "olist_orders_dataset.csv",
        ["order_id", "customer_id", "order_status", "order_purchase_timestamp",
         "order_approved_at", "order_delivered_carrier_date",
         "order_delivered_customer_date", "order_estimated_delivery_date"],
    ),
    "raw_order_items": (
        "olist_order_items_dataset.csv",
        ["order_id", "order_item_id", "product_id", "seller_id",
         "shipping_limit_date", "price", "freight_value"],
    ),
    "raw_order_payments": (
        "olist_order_payments_dataset.csv",
        ["order_id", "payment_sequential", "payment_type",
         "payment_installments", "payment_value"],
    ),
    "raw_order_reviews": (
        "olist_order_reviews_dataset.csv",
        ["review_id", "order_id", "review_score", "review_creation_date",
         "review_answer_timestamp"],
    ),
    "raw_customers": (
        "olist_customers_dataset.csv",
        ["customer_id", "customer_unique_id", "customer_zip_code_prefix",
         "customer_city", "customer_state"],
    ),
    "raw_sellers": (
        "olist_sellers_dataset.csv",
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
    ),
    "raw_products": (
        "olist_products_dataset.csv",
        ["product_id", "product_category_name", "product_weight_g"],
    ),
    "raw_category_translation": (
        "product_category_name_translation.csv",
        ["product_category_name", "product_category_name_english"],
    ),
    "raw_geolocation": (
        "olist_geolocation_dataset.csv",
        ["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng",
         "geolocation_city", "geolocation_state"],
    ),
}

# Order matters: staging first, then the mart that depends on it.
STAGING_SQL = [
    "stg_orders.sql",
    "stg_order_items.sql",
    "stg_order_payments.sql",
    "stg_order_reviews.sql",
    "stg_customers.sql",
    "stg_products.sql",
    "stg_sellers.sql",
]
MART_SQL = ["mart_orders.sql"]
