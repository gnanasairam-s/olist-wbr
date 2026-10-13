-- Q1. Month-over-month revenue and growth %.
-- Revenue = item price + freight of orders that actually sold something
-- (is_revenue_order = 1, i.e. not canceled/unavailable). We use the item table rather
-- than payments so credit-card installment interest isn't counted as revenue.
--
-- The dataset starts and ends with near-empty months (Sep/Dec 2016, Sep 2018) and
-- Nov 2016 is missing completely. A growth % against those is meaningless (+697,000%),
-- so growth is only shown when BOTH months are full (>= 100 orders) AND the previous
-- row really is the previous calendar month.
WITH monthly AS (
    SELECT purchase_month,
           COUNT(*)                   AS orders,
           ROUND(SUM(order_value), 2) AS revenue
    FROM mart_orders
    WHERE is_revenue_order = 1
    GROUP BY purchase_month
),
with_prev AS (
    SELECT m.*,
           LAG(purchase_month) OVER (ORDER BY purchase_month) AS prev_month,
           LAG(orders)         OVER (ORDER BY purchase_month) AS prev_orders,
           LAG(revenue)        OVER (ORDER BY purchase_month) AS prev_revenue
    FROM monthly m
)
SELECT
    purchase_month,
    orders,
    revenue,
    prev_revenue,
    CASE WHEN orders >= 100 AND prev_orders >= 100
          AND prev_month = STRFTIME('%Y-%m', DATE(purchase_month || '-01', '-1 month'))
         THEN ROUND(100.0 * (revenue - prev_revenue) / prev_revenue, 1)
    END                                             AS mom_growth_pct,
    CASE WHEN orders < 100 THEN 1 ELSE 0 END        AS is_partial_month
FROM with_prev
ORDER BY purchase_month;
