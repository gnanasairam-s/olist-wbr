-- CHECK 04: referential integrity -- every order must point to a real customer.
-- Blocking (0 allowed): orphan orders can't be assigned to a state or a repeat buyer.
SELECT
    SUM(CASE WHEN c.customer_id IS NULL THEN 1 ELSE 0 END) AS failed_rows,
    COUNT(*)                                               AS checked_rows
FROM stg_orders o
LEFT JOIN stg_customers c ON c.customer_id = o.customer_id;
