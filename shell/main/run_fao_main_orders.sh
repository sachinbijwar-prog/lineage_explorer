#!/usr/bin/env bash
set -euo pipefail
APP_HOME="${APP_HOME:-/opt/trading-dw}"
"${APP_HOME}/shell/common/common_sql_runner.sh" "FAO_MAIN_ORDERS_LOAD" "${APP_HOME}/sql/main/build_fao_main_orders.sql"
