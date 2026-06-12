#!/usr/bin/env bash
set -euo pipefail
APP_HOME="${APP_HOME:-/opt/trading-dw}"
"${APP_HOME}/shell/common/common_sql_runner.sh" "CDS_MAIN_ORDERS_LOAD" "${APP_HOME}/sql/main/build_cds_main_orders.sql"
