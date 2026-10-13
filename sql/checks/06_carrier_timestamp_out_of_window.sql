-- CHECK 06 (own): the carrier hand-off must sit between purchase and customer delivery.
-- Raw data has impossible scans; staging nulls them. Blocking (0 allowed) after the fix.
SELECT
    SUM(CASE WHEN carrier_ts < purchase_ts
               OR (delivered_ts IS NOT NULL AND carrier_ts > delivered_ts)
             THEN 1 ELSE 0 END)                                AS failed_rows,
    SUM(CASE WHEN carrier_ts IS NOT NULL THEN 1 ELSE 0 END)    AS checked_rows
FROM stg_orders;
