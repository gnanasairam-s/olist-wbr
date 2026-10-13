-- mart_orders: the analysis-ready table. Exactly ONE row per order.
--
-- How we avoid double counting:
--   items, payments and reviews are each rolled up to order level in their own CTE
--   BEFORE joining. Joining items x payments directly would multiply rows whenever an
--   order has 2 items and 2 payment lines, and revenue would be inflated.
DROP TABLE IF EXISTS mart_orders;
CREATE TABLE mart_orders AS
WITH items AS (
    SELECT order_id,
           COUNT(*)                          AS item_count,
           COUNT(DISTINCT seller_id)         AS seller_count,
           ROUND(SUM(price), 2)              AS items_price,
           ROUND(SUM(freight_value), 2)      AS items_freight
    FROM stg_order_items
    GROUP BY order_id
),
payments AS (
    SELECT order_id,
           ROUND(SUM(payment_value), 2)      AS payment_total,
           MAX(payment_installments)         AS max_installments,
           -- the payment line with the biggest value decides the "main" payment type
           (SELECT p2.payment_type FROM stg_order_payments p2
             WHERE p2.order_id = p.order_id
             ORDER BY p2.payment_value DESC LIMIT 1) AS main_payment_type
    FROM stg_order_payments p
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_state,
    o.order_status,
    o.purchase_ts,
    DATE(o.purchase_ts)                                         AS purchase_date,
    STRFTIME('%Y-%m', o.purchase_ts)                            AS purchase_month,
    COALESCE(i.item_count, 0)                                   AS item_count,
    COALESCE(i.seller_count, 0)                                 AS seller_count,
    COALESCE(i.items_price, 0)                                  AS items_price,
    COALESCE(i.items_freight, 0)                                AS items_freight,
    ROUND(COALESCE(i.items_price, 0) + COALESCE(i.items_freight, 0), 2) AS order_value,
    p.payment_total,
    p.max_installments,
    p.main_payment_type,
    CASE WHEN i.order_id IS NOT NULL AND p.order_id IS NOT NULL
          AND ABS(p.payment_total - ROUND(i.items_price + i.items_freight, 2)) > 0.01
         THEN 1 ELSE 0 END                                      AS is_payment_mismatch,
    -- "revenue order" = something was actually sold: not cancelled/unavailable and has items
    CASE WHEN o.order_status NOT IN ('canceled', 'unavailable') AND i.order_id IS NOT NULL
         THEN 1 ELSE 0 END                                      AS is_revenue_order,
    o.approved_ts,
    o.carrier_ts,
    o.delivered_ts,
    o.estimated_delivery_ts,
    CASE WHEN o.delivered_ts IS NOT NULL
         THEN ROUND(JULIANDAY(o.delivered_ts) - JULIANDAY(o.purchase_ts), 2) END
                                                                AS delivery_days,
    -- whole days late vs the date promised at checkout (negative = arrived early)
    CASE WHEN o.delivered_ts IS NOT NULL
         THEN CAST(JULIANDAY(DATE(o.delivered_ts)) - JULIANDAY(DATE(o.estimated_delivery_ts)) AS INTEGER) END
                                                                AS delay_days,
    CASE WHEN o.delivered_ts IS NULL THEN NULL
         WHEN DATE(o.delivered_ts) > DATE(o.estimated_delivery_ts) THEN 1 ELSE 0 END
                                                                AS is_late,
    o.is_delivered_date_missing,
    o.is_carrier_ts_fixed,
    r.review_score
FROM stg_orders o
LEFT JOIN stg_customers     c ON c.customer_id = o.customer_id
LEFT JOIN items             i ON i.order_id    = o.order_id
LEFT JOIN payments          p ON p.order_id    = o.order_id
LEFT JOIN stg_order_reviews r ON r.order_id    = o.order_id;

CREATE UNIQUE INDEX ux_mart_orders ON mart_orders(order_id);
CREATE INDEX ix_mart_orders_date ON mart_orders(purchase_date);

-- Item-level fact used by the category query (Part C Q2). Kept separate so
-- mart_orders stays strictly one row per order.
DROP TABLE IF EXISTS mart_order_items;
CREATE TABLE mart_order_items AS
SELECT
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    pr.category,
    m.customer_state,
    m.purchase_month,
    m.is_revenue_order,
    i.price,
    i.freight_value
FROM stg_order_items i
JOIN mart_orders      m  ON m.order_id   = i.order_id
LEFT JOIN stg_products pr ON pr.product_id = i.product_id;
