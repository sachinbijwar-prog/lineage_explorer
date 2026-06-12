#!/usr/bin/env bash
set -euo pipefail

JOB_NAME="${1:-}"
SQL_FILE="${2:-}"
APP_HOME="${APP_HOME:-/opt/trading-dw}"
CONFIG_FILE="${CONFIG_FILE:-${APP_HOME}/config/application.properties}"

if [ -z "$JOB_NAME" ] || [ -z "$SQL_FILE" ]; then
  echo "usage: common_sql_runner.sh <job_name> <sql_file>"
  exit 2
fi

if [ -f "$CONFIG_FILE" ]; then
  set -a
  . "$CONFIG_FILE"
  set +a
fi

LOG_PATH="${LOG_PATH:-${APP_HOME}/logs}"
DATABASE_NAME="${DATABASE_NAME:-TRADING_DW}"
SCHEMA_NAME="${SCHEMA_NAME:-DWH_TRADING}"
mkdir -p "$LOG_PATH"

LOG_FILE="${LOG_PATH}/${JOB_NAME}_$(date +%Y%m%d_%H%M%S).log"

echo "$(date '+%Y-%m-%d %H:%M:%S') starting ${JOB_NAME}" | tee -a "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') sql_file=${SQL_FILE}" | tee -a "$LOG_FILE"

if [ ! -f "$SQL_FILE" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') missing SQL file ${SQL_FILE}" | tee -a "$LOG_FILE"
  exit 3
fi

beeline \
  --showHeader=false \
  --silent=false \
  --hivevar DATABASE_NAME="$DATABASE_NAME" \
  --hivevar SCHEMA_NAME="$SCHEMA_NAME" \
  -f "$SQL_FILE" >> "$LOG_FILE" 2>&1

RC=$?
if [ "$RC" -eq 0 ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') completed ${JOB_NAME}" | tee -a "$LOG_FILE"
else
  echo "$(date '+%Y-%m-%d %H:%M:%S') failed ${JOB_NAME} rc=${RC}" | tee -a "$LOG_FILE"
fi

exit "$RC"
