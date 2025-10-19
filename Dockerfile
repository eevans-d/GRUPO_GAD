# Fly.io optimized Dockerfile for GRUPO_GAD
# Multi-stage build for minimal image size

FROM python:3.12-slim AS builder

# Build environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies (added postgresql libs for psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# === Runtime Stage ===
FROM python:3.12-slim

# Runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:$PATH" \
    PORT=8080

WORKDIR /app

# Install runtime dependencies (added postgresql libs for runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code (ensure all necessary files are copied)
COPY alembic.ini ./
COPY alembic ./alembic
COPY config ./config
COPY src ./src
COPY dashboard ./dashboard
COPY templates ./templates

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Create non-root user for security
RUN groupadd -r app && \
    useradd -r -g app app && \
    chown -R app:app /app

# Switch to non-root user
USER app

# Expose port (Fly.io uses 8080 internally)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start command (overridden by fly.toml release_command for migrations)
CMD ["uvicorn", "src.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--log-level", "info"]
