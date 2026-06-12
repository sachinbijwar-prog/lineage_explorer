#!/usr/bin/env bash
set -euo pipefail
APP_HOME="${APP_HOME:-/opt/trading-dw}"
"${APP_HOME}/shell/common/common_sql_runner.sh" "DIM_CLIENT_MASTER_LOAD" "${APP_HOME}/sql/dimensions/build_dim_client.sql"
