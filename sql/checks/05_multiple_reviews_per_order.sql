-- CHECK 05 (own): at most one review per order after staging.
-- Raw data has 547 orders with 2-3 reviews; staging keeps the latest one.
-- Blocking (0 allowed): otherwise average review score per order is double counted.
SELECT
    COUNT(*) AS failed_rows,
    (SELECT COUNT(*) FROM stg_order_reviews) AS checked_rows
FROM (SELECT order_id FROM stg_order_reviews GROUP BY order_id HAVING COUNT(*) > 1);
