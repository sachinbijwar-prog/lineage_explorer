-- Stage raw transaction records
CREATE TABLE STG_SALES AS
SELECT 
    tx_id,
    cust_id,
    prod_id,
    store_id,
    quantity,
    amount,
    tx_timestamp
FROM ERP_SALES;
