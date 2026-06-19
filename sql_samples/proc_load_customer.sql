-- Merge staging records into dimension table
MERGE INTO DIM_CUSTOMER AS target
USING STG_CUSTOMER AS source
ON target.cust_id = source.cust_id
WHEN MATCHED THEN
    UPDATE SET 
        target.first_name = source.first_name,
        target.last_name = source.last_name,
        target.email = source.email
WHEN NOT MATCHED THEN
    INSERT (cust_id, first_name, last_name, email)
    VALUES (source.cust_id, source.first_name, source.last_name, source.email);
