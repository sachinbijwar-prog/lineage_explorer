#!/usr/bin/env bash
set -euo pipefail
APP_HOME="${APP_HOME:-/opt/trading-dw}"
"${APP_HOME}/shell/common/common_sql_runner.sh" "COM_S2_ORDER_STAGE_LOAD" "${APP_HOME}/sql/stage/build_com_stage.sql"
