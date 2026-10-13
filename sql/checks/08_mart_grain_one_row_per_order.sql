-- CHECK 08 (own, runs after the mart is built): mart_orders must have exactly one row
-- per staged order. If a join fans out, this catches it before anyone reads a dashboard.
SELECT
    ABS((SELECT COUNT(*) FROM mart_orders) - (SELECT COUNT(*) FROM stg_orders))
  + (SELECT COUNT(*) FROM (SELECT order_id FROM mart_orders GROUP BY order_id HAVING COUNT(*) > 1))
        AS failed_rows,
    (SELECT COUNT(*) FROM mart_orders) AS checked_rows;
