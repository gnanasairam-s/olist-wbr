-- stg_customers: customer_id is per ORDER in Olist (a new one is issued every purchase).
-- customer_unique_id is the real person; keep both.
DROP TABLE IF EXISTS stg_customers;
CREATE TABLE stg_customers AS
SELECT DISTINCT
    TRIM(customer_id)                 AS customer_id,
    TRIM(customer_unique_id)          AS customer_unique_id,
    customer_zip_code_prefix,
    LOWER(TRIM(customer_city))        AS customer_city,
    UPPER(TRIM(customer_state))       AS customer_state
FROM raw_customers
WHERE customer_id IS NOT NULL;
CREATE UNIQUE INDEX ux_stg_customers ON stg_customers(customer_id);
