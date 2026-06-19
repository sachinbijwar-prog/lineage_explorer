-- Build integrated view of customer transactions and ratings
CREATE VIEW VW_CUSTOMER_360 AS
SELECT 
    c.cust_id,
    c.first_name,
    c.last_name,
    COALESCE(SUM(s.amount), 0) AS lifetime_value,
    COALESCE(AVG(i.rating), 5.0) AS avg_satisfaction_rating
FROM DIM_CUSTOMER c
LEFT JOIN FACT_SALES s ON c.cust_id = s.cust_id
LEFT JOIN STG_INTERACTIONS i ON c.cust_id = i.cust_id
GROUP BY c.cust_id, c.first_name, c.last_name;
