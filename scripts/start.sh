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

exec uvicorn \
	src.api.main:app \
	--workers "$WORKERS" \
	--host 0.0.0.0 \
	--port 8000 \
	--log-level info
