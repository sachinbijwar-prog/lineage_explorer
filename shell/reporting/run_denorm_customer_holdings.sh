#!/usr/bin/env bash
set -euo pipefail
APP_HOME="${APP_HOME:-/opt/trading-dw}"
"${APP_HOME}/shell/common/common_sql_runner.sh" "DENORM_CUSTOMER_HOLDINGS_LOAD" "${APP_HOME}/sql/reporting/build_denorm_customer_holdings.sql"
