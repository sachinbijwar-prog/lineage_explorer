-- Build core enterprise fact table
INSERT INTO FACT_SALES
SELECT 
    s.tx_id,
    c.cust_id,
    p.prod_id,
    d.store_id,
    s.quantity,
    s.amount,
    s.tx_timestamp
FROM STG_SALES s
JOIN DIM_CUSTOMER c ON s.cust_id = c.cust_id
JOIN DIM_PRODUCT p ON s.prod_id = p.prod_id
JOIN DIM_STORE d ON s.store_id = d.store_id;
