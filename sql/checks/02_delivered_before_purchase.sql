-- CHECK 02: a parcel cannot reach the customer before it was bought.
-- Blocking (0 allowed).
SELECT
    SUM(CASE WHEN delivered_ts < purchase_ts THEN 1 ELSE 0 END) AS failed_rows,
    SUM(CASE WHEN delivered_ts IS NOT NULL THEN 1 ELSE 0 END)   AS checked_rows
FROM stg_orders;
