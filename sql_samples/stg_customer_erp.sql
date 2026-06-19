-- Ingest raw customer transactions from the ERP database
INSERT INTO STG_CUSTOMER
SELECT 
    cust_id,
    first_name,
    last_name,
    email,
    created_at
FROM ERP_CUSTOMER;
