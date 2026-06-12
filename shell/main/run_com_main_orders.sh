#!/usr/bin/env bash
set -euo pipefail
APP_HOME="${APP_HOME:-/opt/trading-dw}"
"${APP_HOME}/shell/common/common_sql_runner.sh" "COM_MAIN_ORDERS_LOAD" "${APP_HOME}/sql/main/build_com_main_orders.sql"
