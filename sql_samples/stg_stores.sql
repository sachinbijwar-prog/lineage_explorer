-- Stage physical store locations
CREATE TABLE STG_STORES AS
SELECT 
    store_id,
    store_name,
    city,
    region
FROM ERP_STORES;
