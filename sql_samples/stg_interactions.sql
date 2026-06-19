-- Stage CRM support and interaction touchpoints
CREATE TABLE STG_INTERACTIONS AS
SELECT 
    interaction_id,
    contact_id AS cust_id,
    channel,
    rating,
    created_date
FROM CRM_INTERACTIONS;
