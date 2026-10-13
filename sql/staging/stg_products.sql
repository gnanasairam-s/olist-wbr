-- stg_products: adds the English category name. 610 products have no category in the
-- source; we label them 'unknown' instead of dropping their sales.
DROP TABLE IF EXISTS stg_products;
CREATE TABLE stg_products AS
SELECT
    TRIM(p.product_id)                                             AS product_id,
    COALESCE(p.product_category_name, 'unknown')                   AS category_pt,
    COALESCE(t.product_category_name_english,
             p.product_category_name, 'unknown')                   AS category,
    CAST(p.product_weight_g AS REAL)                               AS weight_g
FROM raw_products p
LEFT JOIN raw_category_translation t
       ON t.product_category_name = p.product_category_name;
CREATE UNIQUE INDEX ux_stg_products ON stg_products(product_id);
