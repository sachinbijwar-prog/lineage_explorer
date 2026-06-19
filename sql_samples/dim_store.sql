-- Populate DIM_STORE dimension
INSERT INTO DIM_STORE
SELECT 
    store_id,
    store_name,
    city,
    region,
    'ACTIVE' AS status
FROM STG_STORES;
