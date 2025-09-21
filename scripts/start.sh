#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting Uvicorn server..."

# Calculate workers: (2 x CPU) + 1, minimum 3
CPU_COUNT=$(getconf _NPROCESSORS_ONLN || echo 2)
WORKERS=$((CPU_COUNT * 2 + 1))
if [ "$WORKERS" -lt 3 ]; then
	WORKERS=3
fi

exec gunicorn \
	src.api.main:app \
	--workers "$WORKERS" \
	--worker-class uvicorn.workers.UvicornWorker \
	--bind 0.0.0.0:8000 \
	--timeout 60 \
	--graceful-timeout 30 \
	--keep-alive 5 \
	--log-level info
