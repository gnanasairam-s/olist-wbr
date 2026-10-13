-- stg_orders: one row per order, typed and cleaned.
-- Fixes applied here (see report, Part B):
--   * order_delivered_carrier_date is set to NULL when it falls before the purchase
--     or after the customer received the parcel. Those 189 timestamps are impossible
--     and look like carrier-scan errors; the rest of the order is fine so we keep it.
--   * is_delivered_date_missing flags 'delivered' orders that have no delivery date (8 rows).
--     They stay in the table but are left out of delivery-time metrics.
DROP TABLE IF EXISTS stg_orders;
CREATE TABLE stg_orders AS
WITH typed AS (
    SELECT
        TRIM(order_id)                                   AS order_id,
        TRIM(customer_id)                                AS customer_id,
        LOWER(TRIM(order_status))                        AS order_status,
        DATETIME(order_purchase_timestamp)               AS purchase_ts,
        DATETIME(order_approved_at)                      AS approved_ts,
        DATETIME(order_delivered_carrier_date)           AS carrier_ts_raw,
        DATETIME(order_delivered_customer_date)          AS delivered_ts,
        DATETIME(order_estimated_delivery_date)          AS estimated_delivery_ts,
        ROW_NUMBER() OVER (PARTITION BY TRIM(order_id)
                           ORDER BY order_purchase_timestamp) AS rn
    FROM raw_orders
    WHERE order_id IS NOT NULL AND TRIM(order_id) <> ''
)
SELECT
    order_id,
    customer_id,
    order_status,
    purchase_ts,
    approved_ts,
    CASE WHEN carrier_ts_raw < purchase_ts
           OR (delivered_ts IS NOT NULL AND carrier_ts_raw > delivered_ts)
         THEN NULL ELSE carrier_ts_raw END                AS carrier_ts,
    CASE WHEN carrier_ts_raw < purchase_ts
           OR (delivered_ts IS NOT NULL AND carrier_ts_raw > delivered_ts)
         THEN 1 ELSE 0 END                                AS is_carrier_ts_fixed,
    delivered_ts,
    estimated_delivery_ts,
    CASE WHEN order_status = 'delivered' AND delivered_ts IS NULL
         THEN 1 ELSE 0 END                                AS is_delivered_date_missing
FROM typed
WHERE rn = 1;
CREATE UNIQUE INDEX ux_stg_orders ON stg_orders(order_id);
