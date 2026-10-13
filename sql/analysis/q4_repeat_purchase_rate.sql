-- Q4. Repeat-purchase rate.
-- customer_id is NOT the customer: Olist issues a new customer_id for every order,
-- so counting by it gives ~0% repeat. customer_unique_id is the actual person.
-- We count only orders that went through (is_revenue_order = 1).
WITH per_customer AS (
    SELECT customer_unique_id,
           COUNT(DISTINCT order_id) AS n_orders
    FROM mart_orders
    WHERE is_revenue_order = 1
    GROUP BY customer_unique_id
),
wrong_key AS (   -- shown only to prove the point
    SELECT COUNT(*) AS n_ids,
           SUM(CASE WHEN n > 1 THEN 1 ELSE 0 END) AS repeaters
    FROM (SELECT customer_id, COUNT(*) AS n FROM mart_orders
          WHERE is_revenue_order = 1 GROUP BY customer_id)
)
SELECT
    COUNT(*)                                             AS customers,
    SUM(CASE WHEN n_orders >= 2 THEN 1 ELSE 0 END)       AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN n_orders >= 2 THEN 1 ELSE 0 END) / COUNT(*), 2)
                                                         AS repeat_rate_pct,
    MAX(n_orders)                                        AS max_orders_one_customer,
    (SELECT ROUND(100.0 * repeaters / n_ids, 2) FROM wrong_key)
                                                         AS repeat_rate_if_using_customer_id_pct
FROM per_customer;
