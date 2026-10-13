-- Q5. Average delivery delay vs the estimated date, and how it relates to review score.
-- delay_days = delivered date - estimated date (negative = early).
-- Only delivered orders with a real delivery date and a review.
WITH base AS (
    SELECT delay_days, review_score,
           CASE
               WHEN delay_days <= -7 THEN '1. 7+ days early'
               WHEN delay_days <   0 THEN '2. 1-6 days early'
               WHEN delay_days =   0 THEN '3. on the day'
               WHEN delay_days <=  3 THEN '4. 1-3 days late'
               WHEN delay_days <=  7 THEN '5. 4-7 days late'
               WHEN delay_days <= 14 THEN '6. 8-14 days late'
               ELSE                       '7. 15+ days late'
           END AS delay_bucket
    FROM mart_orders
    WHERE order_status = 'delivered'
      AND delivered_ts IS NOT NULL
      AND review_score IS NOT NULL
)
SELECT
    delay_bucket,
    COUNT(*)                                                          AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)                AS pct_of_orders,
    ROUND(AVG(delay_days), 1)                                         AS avg_delay_days,
    ROUND(AVG(review_score), 2)                                       AS avg_review,
    ROUND(100.0 * AVG(CASE WHEN review_score <= 2 THEN 1.0 ELSE 0 END), 1) AS pct_1_2_star
FROM base
GROUP BY delay_bucket
UNION ALL
SELECT
    'ALL delivered', COUNT(*), 100.0,
    ROUND(AVG(delay_days), 1), ROUND(AVG(review_score), 2),
    ROUND(100.0 * AVG(CASE WHEN review_score <= 2 THEN 1.0 ELSE 0 END), 1)
FROM base
ORDER BY delay_bucket;
