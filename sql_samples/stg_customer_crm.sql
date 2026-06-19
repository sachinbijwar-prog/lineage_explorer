-- Ingest raw contact details from the CRM database
INSERT INTO STG_CUSTOMER
SELECT 
    contact_id AS cust_id,
    first_name,
    last_name,
    email_address AS email,
    update_date AS created_at
FROM CRM_CONTACTS;
