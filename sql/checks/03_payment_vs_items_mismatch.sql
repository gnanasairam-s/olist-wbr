-- CHECK 03: what the customer paid should equal item price + freight (1 cent tolerance).
-- Known cause in this dataset: credit-card installment interest and voucher rounding,
-- so these orders are FLAGGED (mart_orders.is_payment_mismatch), not dropped.
-- Alarm fires if more than 1% of orders mismatch -- that would mean a broken feed, not interest.
WITH it AS (
    SELECT order_id, SUM(price) + SUM(freight_value) AS items_total
    FROM stg_order_items GROUP BY order_id
),
pay AS (
    SELECT order_id, SUM(payment_value) AS paid
    FROM stg_order_payments GROUP BY order_id
)
SELECT
    SUM(CASE WHEN ABS(ROUND(pay.paid, 2) - ROUND(it.items_total, 2)) > 0.01 THEN 1 ELSE 0 END) AS failed_rows,
    COUNT(*)                                                             AS checked_rows
FROM it JOIN pay USING (order_id);
