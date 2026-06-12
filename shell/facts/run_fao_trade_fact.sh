#!/usr/bin/env bash
set -euo pipefail
APP_HOME="${APP_HOME:-/opt/trading-dw}"
"${APP_HOME}/shell/common/common_sql_runner.sh" "FAO_TRADE_FACT_LOAD" "${APP_HOME}/sql/facts/build_fao_trade_fact.sql"
