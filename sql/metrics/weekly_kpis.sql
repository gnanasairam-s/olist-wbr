-- Weekly Business Review KPIs (Part D). One row per ISO week (Monday start), by purchase week.
--
-- NORTH STAR  happy_delivered_orders = orders delivered ON/BEFORE the promised date
--                                      AND rated 4-5 stars
-- SUPPORTING  gmv                    = SUM(price + freight) of non-canceled orders with items
--             on_time_rate           = delivered on/before estimate / delivered orders (with a date)
-- GUARDRAILS  bad_review_rate        = reviews with 1-2 stars / all reviews
--             cancel_rate            = canceled or unavailable orders / all orders
-- (Repeat-purchase rate is a slow metric, so it is tracked monthly, see q4.)
--
-- Note: reviews arrive ~1-2 weeks after delivery, so the latest 2-3 weeks are
-- always incomplete. The WBR should read them as provisional.
SELECT
    DATE(purchase_ts, 'weekday 0', '-6 days')                               AS week_start,
    COUNT(*)                                                                AS orders,
    SUM(CASE WHEN order_status = 'delivered' AND is_late = 0
              AND review_score >= 4 THEN 1 ELSE 0 END)                      AS happy_delivered_orders,
    ROUND(SUM(CASE WHEN is_revenue_order = 1 THEN order_value ELSE 0 END), 2) AS gmv,
    ROUND(100.0 * SUM(CASE WHEN is_late = 0 THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN is_late IS NOT NULL THEN 1 ELSE 0 END), 0), 1) AS on_time_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END)
          / NULLIF(SUM(CASE WHEN review_score IS NOT NULL THEN 1 ELSE 0 END), 0), 1) AS bad_review_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN order_status IN ('canceled', 'unavailable') THEN 1 ELSE 0 END)
          / COUNT(*), 2)                                                    AS cancel_rate_pct
FROM mart_orders
GROUP BY week_start
ORDER BY week_start;
