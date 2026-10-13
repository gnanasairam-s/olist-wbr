-- CHECK 07 (own): an order marked 'delivered' should carry a delivery date.
-- Flagged (is_delivered_date_missing) and left out of delivery metrics.
-- Alarm if more than 0.1% of delivered orders are affected.
SELECT
    SUM(CASE WHEN delivered_ts IS NULL THEN 1 ELSE 0 END) AS failed_rows,
    COUNT(*)                                              AS checked_rows
FROM stg_orders
WHERE order_status = 'delivered';
