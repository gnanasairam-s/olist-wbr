DROP TABLE IF EXISTS stg_sellers;
CREATE TABLE stg_sellers AS
SELECT DISTINCT
    TRIM(seller_id)               AS seller_id,
    seller_zip_code_prefix,
    LOWER(TRIM(seller_city))      AS seller_city,
    UPPER(TRIM(seller_state))     AS seller_state
FROM raw_sellers;
CREATE UNIQUE INDEX ux_stg_sellers ON stg_sellers(seller_id);
