-- Build daily aggregated summary reporting view
CREATE VIEW VW_SALES_SUMMARY AS
SELECT 
    prod_id,
    store_id,
    SUM(quantity) AS total_qty,
    SUM(amount) AS total_sales_amt,
    COUNT(tx_id) AS tx_count
FROM FACT_SALES
GROUP BY prod_id, store_id;
