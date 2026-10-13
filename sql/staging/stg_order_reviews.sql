-- stg_order_reviews: exactly ONE review per order.
-- 547 orders have 2-3 reviews in the raw file (customer edited / re-submitted).
-- We keep the most recent answer because it reflects the customer's final opinion.
DROP TABLE IF EXISTS stg_order_reviews;
CREATE TABLE stg_order_reviews AS
WITH ranked AS (
    SELECT
        TRIM(review_id)                       AS review_id,
        TRIM(order_id)                        AS order_id,
        CAST(review_score AS INTEGER)         AS review_score,
        DATETIME(review_creation_date)        AS review_created_ts,
        DATETIME(review_answer_timestamp)     AS review_answered_ts,
        ROW_NUMBER() OVER (PARTITION BY TRIM(order_id)
                           ORDER BY review_answer_timestamp DESC,
                                    review_creation_date DESC,
                                    review_id) AS rn
    FROM raw_order_reviews
    WHERE order_id IS NOT NULL
      AND CAST(review_score AS INTEGER) BETWEEN 1 AND 5
)
SELECT review_id, order_id, review_score, review_created_ts, review_answered_ts
FROM ranked
WHERE rn = 1;
CREATE UNIQUE INDEX ux_stg_reviews_order ON stg_order_reviews(order_id);
