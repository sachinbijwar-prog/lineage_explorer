# Trading Platform Data Warehouse Lineage

This document summarizes the lineage that is discoverable from SQL statements, shell invocations, and cron schedules in this repository.

## Table Lineage

FAO_S1_RAW_ORDERS -> FAO_S2_ORDER_STAGE -> FAO_MAIN_ORDERS -> DENORM_CLIENT_POSITION

CM_S1_RAW_ORDERS -> CM_S2_ORDER_STAGE -> CM_MAIN_ORDERS -> DENORM_CUSTOMER_HOLDINGS

CDS_S1_RAW_ORDERS -> CDS_S2_ORDER_STAGE -> CDS_MAIN_ORDERS

COM_S1_RAW_ORDERS -> COM_S2_ORDER_STAGE -> COM_MAIN_ORDERS

FAO_S1_RAW_ORDERS -> FAO_TRADE_FACT

CM_S1_RAW_ORDERS -> CM_TRADE_FACT

CDS_S1_RAW_ORDERS -> CDS_TRADE_FACT

COM_S1_RAW_ORDERS -> COM_TRADE_FACT

DIM_CLIENT_MASTER -> FAO_MAIN_ORDERS
DIM_CLIENT_MASTER -> CM_MAIN_ORDERS
DIM_CLIENT_MASTER -> CDS_MAIN_ORDERS
DIM_CLIENT_MASTER -> COM_MAIN_ORDERS
DIM_CLIENT_MASTER -> FAO_TRADE_FACT
DIM_CLIENT_MASTER -> CM_TRADE_FACT
DIM_CLIENT_MASTER -> CDS_TRADE_FACT
DIM_CLIENT_MASTER -> COM_TRADE_FACT
DIM_CLIENT_MASTER -> DENORM_CLIENT_POSITION
DIM_CLIENT_MASTER -> DENORM_CUSTOMER_HOLDINGS

DIM_SECURITY_MASTER -> FAO_MAIN_ORDERS
DIM_SECURITY_MASTER -> CM_MAIN_ORDERS
DIM_SECURITY_MASTER -> CDS_MAIN_ORDERS
DIM_SECURITY_MASTER -> COM_MAIN_ORDERS
DIM_SECURITY_MASTER -> FAO_TRADE_FACT
DIM_SECURITY_MASTER -> CM_TRADE_FACT
DIM_SECURITY_MASTER -> CDS_TRADE_FACT
DIM_SECURITY_MASTER -> COM_TRADE_FACT

DIM_DMO_CALENDAR -> FAO_MAIN_ORDERS
DIM_DMO_CALENDAR -> CM_MAIN_ORDERS
DIM_DMO_CALENDAR -> CDS_MAIN_ORDERS
DIM_DMO_CALENDAR -> COM_MAIN_ORDERS
DIM_DMO_CALENDAR -> FAO_TRADE_FACT
DIM_DMO_CALENDAR -> CM_TRADE_FACT
DIM_DMO_CALENDAR -> CDS_TRADE_FACT
DIM_DMO_CALENDAR -> COM_TRADE_FACT

## Job Lineage

run_dim_client.sh -> common_sql_runner.sh -> build_dim_client.sql -> DIM_CLIENT_MASTER

run_dim_security.sh -> common_sql_runner.sh -> build_dim_security.sql -> DIM_SECURITY_MASTER

run_dim_calendar.sh -> common_sql_runner.sh -> build_dim_calendar.sql -> DIM_DMO_CALENDAR

run_fao_stage.sh -> common_sql_runner.sh -> build_fao_stage.sql -> FAO_S2_ORDER_STAGE

run_cm_stage.sh -> common_sql_runner.sh -> build_cm_stage.sql -> CM_S2_ORDER_STAGE

run_cds_stage.sh -> common_sql_runner.sh -> build_cds_stage.sql -> CDS_S2_ORDER_STAGE

run_com_stage.sh -> common_sql_runner.sh -> build_com_stage.sql -> COM_S2_ORDER_STAGE

run_fao_trade_fact.sh -> common_sql_runner.sh -> build_fao_trade_fact.sql -> FAO_TRADE_FACT

run_cm_trade_fact.sh -> common_sql_runner.sh -> build_cm_trade_fact.sql -> CM_TRADE_FACT

run_cds_trade_fact.sh -> common_sql_runner.sh -> build_cds_trade_fact.sql -> CDS_TRADE_FACT

run_com_trade_fact.sh -> common_sql_runner.sh -> build_com_trade_fact.sql -> COM_TRADE_FACT

run_fao_main_orders.sh -> common_sql_runner.sh -> build_fao_main_orders.sql -> FAO_MAIN_ORDERS

run_cm_main_orders.sh -> common_sql_runner.sh -> build_cm_main_orders.sql -> CM_MAIN_ORDERS

run_cds_main_orders.sh -> common_sql_runner.sh -> build_cds_main_orders.sql -> CDS_MAIN_ORDERS

run_com_main_orders.sh -> common_sql_runner.sh -> build_com_main_orders.sql -> COM_MAIN_ORDERS

run_denorm_client_position.sh -> common_sql_runner.sh -> build_denorm_client_position.sql -> DENORM_CLIENT_POSITION

run_denorm_customer_holdings.sh -> common_sql_runner.sh -> build_denorm_customer_holdings.sql -> DENORM_CUSTOMER_HOLDINGS

## Shell Dependencies

All business scripts invoke shell/common/common_sql_runner.sh with a job name and a SQL file path.

The common runner loads config/application.properties, writes execution logs, and calls beeline with the target SQL file.

## SQL Dependencies

Stage SQL reads segment S1 raw order tables and writes segment S2 order stage tables.

Main order SQL reads segment S2 order stage tables plus DIM_CLIENT_MASTER, DIM_SECURITY_MASTER, and DIM_DMO_CALENDAR.

Trade fact SQL reads segment S1 raw order tables plus DIM_CLIENT_MASTER, DIM_SECURITY_MASTER, and DIM_DMO_CALENDAR.

Reporting SQL reads main order tables and DIM_CLIENT_MASTER.

## Execution Flow

1. scheduler/trading_dw_batch.cron starts dimension shell scripts.
2. Dimension shell scripts invoke common_sql_runner.sh and load dimension SQL.
3. Stage shell scripts run after dimensions and load S2 order stage tables.
4. Trade fact shell scripts run after stage loads and read S1 raw orders plus dimensions.
5. Main order shell scripts run after facts and read S2 stage tables plus dimensions.
6. Reporting shell scripts run after main order loads and populate denormalized reporting tables.
