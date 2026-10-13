-- CHECK 01: every order must have an order_id and it must be unique.
-- Blocking (0 failures allowed): a duplicate order_id would double revenue downstream.
SELECT
    (SELECT COUNT(*) FROM stg_orders WHERE order_id IS NULL OR order_id = '')
  + (SELECT COUNT(*) FROM (SELECT order_id FROM stg_orders GROUP BY order_id HAVING COUNT(*) > 1))
        AS failed_rows,
    (SELECT COUNT(*) FROM stg_orders) AS checked_rows;
