-- Same checks as 01-07, run on the untouched raw tables BEFORE cleaning.
-- These numbers go into the report so we can say how many rows were affected
-- and what staging did about them. This query never blocks the pipeline.
WITH it AS (
    SELECT order_id, SUM(CAST(price AS REAL)) + SUM(CAST(freight_value AS REAL)) AS t
    FROM raw_order_items GROUP BY order_id
), pay AS (
    SELECT order_id, SUM(CAST(payment_value AS REAL)) AS p
    FROM raw_order_payments GROUP BY order_id
)
SELECT '01_order_id_null_or_duplicate' AS check_name,
       (SELECT COUNT(*) FROM raw_orders WHERE order_id IS NULL)
     + (SELECT COUNT(*) FROM (SELECT order_id FROM raw_orders GROUP BY order_id HAVING COUNT(*) > 1)) AS failed_rows
UNION ALL
SELECT '02_delivered_before_purchase',
       (SELECT COUNT(*) FROM raw_orders
         WHERE DATETIME(order_delivered_customer_date) < DATETIME(order_purchase_timestamp))
UNION ALL
SELECT '03_payment_vs_items_mismatch',
       (SELECT COUNT(*) FROM it JOIN pay USING (order_id) WHERE ABS(ROUND(p, 2) - ROUND(t, 2)) > 0.01)
UNION ALL
SELECT '04_orders_without_customer',
       (SELECT COUNT(*) FROM raw_orders o
         LEFT JOIN raw_customers c ON c.customer_id = o.customer_id WHERE c.customer_id IS NULL)
UNION ALL
SELECT '05_multiple_reviews_per_order',
       (SELECT COUNT(*) FROM (SELECT order_id FROM raw_order_reviews GROUP BY order_id HAVING COUNT(*) > 1))
UNION ALL
SELECT '06_carrier_timestamp_out_of_window',
       (SELECT COUNT(*) FROM raw_orders
         WHERE DATETIME(order_delivered_carrier_date) < DATETIME(order_purchase_timestamp)
            OR DATETIME(order_delivered_carrier_date) > DATETIME(order_delivered_customer_date))
UNION ALL
SELECT '07_delivered_without_delivery_date',
       (SELECT COUNT(*) FROM raw_orders
         WHERE order_status = 'delivered' AND order_delivered_customer_date IS NULL);
