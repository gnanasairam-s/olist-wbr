-- Q3. 7-day rolling average of daily order count.
-- Days with zero orders still need to be in the window, otherwise "7 rows" would
-- silently cover more than 7 calendar days. So we build a full calendar first.
WITH RECURSIVE bounds AS (
    SELECT MIN(purchase_date) AS d0, MAX(purchase_date) AS d1 FROM mart_orders
),
calendar(day) AS (
    SELECT d0 FROM bounds
    UNION ALL
    SELECT DATE(day, '+1 day') FROM calendar, bounds WHERE day < bounds.d1
),
daily AS (
    SELECT purchase_date AS day, COUNT(*) AS orders
    FROM mart_orders
    GROUP BY purchase_date
),
filled AS (
    SELECT c.day, COALESCE(d.orders, 0) AS orders
    FROM calendar c LEFT JOIN daily d ON d.day = c.day
)
SELECT
    day,
    orders,
    ROUND(AVG(orders) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1)
        AS rolling_7d_avg,
    COUNT(*) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
        AS days_in_window   -- < 7 for the first six days
FROM filled
ORDER BY day;
