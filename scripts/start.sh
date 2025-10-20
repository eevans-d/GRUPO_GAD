#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting Uvicorn server..."

# Decide workers count
# - En desarrollo: 1 worker (WebSockets necesitan un solo proceso si no hay pub/sub)
# - En producción: (2 x CPU) + 1, mínimo 3, a menos que UVICORN_WORKERS esté definido
ENVIRONMENT=${ENVIRONMENT:-development}
if [ -n "$UVICORN_WORKERS" ]; then
	WORKERS=$UVICORN_WORKERS
else
	if [ "$ENVIRONMENT" = "production" ]; then
		CPU_COUNT=$(getconf _NPROCESSORS_ONLN || echo 2)
		WORKERS=$((CPU_COUNT * 2 + 1))
		if [ "$WORKERS" -lt 3 ]; then
			WORKERS=3
		fi
	else
		WORKERS=1
	fi
fi

# Read PORT from environment or default to 8000
PORT=${PORT:-8000}

exec uvicorn \
	src.api.main:app \
	--workers "$WORKERS" \
	--host 0.0.0.0 \
	--port "$PORT" \
	--log-level info
