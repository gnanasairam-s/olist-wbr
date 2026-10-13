-- stg_order_items: one row per (order_id, order_item_id), numeric columns cast to REAL.
DROP TABLE IF EXISTS stg_order_items;
CREATE TABLE stg_order_items AS
SELECT DISTINCT
    TRIM(order_id)                      AS order_id,
    CAST(order_item_id AS INTEGER)      AS order_item_id,
    TRIM(product_id)                    AS product_id,
    TRIM(seller_id)                     AS seller_id,
    DATETIME(shipping_limit_date)       AS shipping_limit_ts,
    CAST(price AS REAL)                 AS price,
    CAST(freight_value AS REAL)         AS freight_value
FROM raw_order_items
WHERE order_id IS NOT NULL;
CREATE INDEX ix_stg_items_order ON stg_order_items(order_id);
