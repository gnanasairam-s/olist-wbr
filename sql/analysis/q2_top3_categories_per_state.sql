-- Q2. Top 3 product categories per customer state, by revenue (price + freight).
-- DENSE_RANK so two categories tied on revenue share a rank instead of one being dropped.
WITH cat_state AS (
    SELECT customer_state,
           category,
           ROUND(SUM(price + freight_value), 2) AS revenue,
           COUNT(DISTINCT order_id)             AS orders
    FROM mart_order_items
    WHERE is_revenue_order = 1
    GROUP BY customer_state, category
),
ranked AS (
    SELECT *,
           DENSE_RANK() OVER (PARTITION BY customer_state ORDER BY revenue DESC) AS rnk
    FROM cat_state
)
SELECT customer_state, rnk, category, revenue, orders
FROM ranked
WHERE rnk <= 3
ORDER BY customer_state, rnk;
