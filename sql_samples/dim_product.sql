-- Populate DIM_PRODUCT dimension
INSERT INTO DIM_PRODUCT
SELECT 
    prod_id,
    sku,
    product_name,
    category,
    price,
    CURRENT_DATE() AS active_date
FROM STG_PRODUCT;
