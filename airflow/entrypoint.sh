#!/usr/bin/env bash
set -euo pipefail

# Clean stale PID files from previous runs.
rm -f "${AIRFLOW_HOME}/airflow-webserver.pid"
rm -f "${AIRFLOW_HOME}/airflow-scheduler.pid"

echo "Initialising Airflow database..."
airflow db migrate

echo "Creating admin user..."
airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@localhost \
  2>/dev/null || true

echo "Starting webserver & scheduler..."
airflow webserver --port 8080 &
airflow scheduler
