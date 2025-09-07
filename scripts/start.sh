#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting Uvicorn server..."
exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
