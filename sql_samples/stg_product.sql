-- Stage product details from the ERP catalog
CREATE TABLE STG_PRODUCT AS
SELECT 
    prod_id,
    sku,
    product_name,
    category,
    price
FROM ERP_PRODUCT;
