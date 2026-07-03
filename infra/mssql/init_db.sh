#!/usr/bin/env bash
# One-shot local-dev bootstrap for the mssql service: waits for SQL Server to
# accept connections, then runs init_db.sql to create the "awa" database and
# the scoped "mssql" app login. Idempotent - safe to re-run (mirrors
# infra/kafka/create_topics.sh's pattern for this compose stack).
set -euo pipefail

SQLCMD="/opt/mssql-tools18/bin/sqlcmd"
HOST="mssql"

until "${SQLCMD}" -S "${HOST}" -U sa -P "${MSSQL_SA_PASSWORD}" -C -Q "SELECT 1" >/dev/null 2>&1; do
  echo "Waiting for SQL Server at ${HOST}..."
  sleep 2
done

"${SQLCMD}" -S "${HOST}" -U sa -P "${MSSQL_SA_PASSWORD}" -C \
  -v AWA_APP_PASSWORD="${AWA_APP_PASSWORD}" \
  -i /init_db.sql

echo "SQL Server database/login initialization complete."
