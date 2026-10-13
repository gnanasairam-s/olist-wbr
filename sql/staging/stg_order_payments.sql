-- stg_order_payments: one row per (order_id, payment_sequential).
-- An order can be paid in several pieces (e.g. voucher + credit card), so never join this
-- table straight onto items -- aggregate to order level first.
DROP TABLE IF EXISTS stg_order_payments;
CREATE TABLE stg_order_payments AS
SELECT DISTINCT
    TRIM(order_id)                          AS order_id,
    CAST(payment_sequential AS INTEGER)     AS payment_sequential,
    LOWER(TRIM(payment_type))               AS payment_type,
    CAST(payment_installments AS INTEGER)   AS payment_installments,
    CAST(payment_value AS REAL)             AS payment_value
FROM raw_order_payments
WHERE order_id IS NOT NULL;
CREATE INDEX ix_stg_pay_order ON stg_order_payments(order_id);
