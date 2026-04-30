# ─────────────────────────────────────────────────────────────────────────────
# ACEest Fitness & Gym — Production Dockerfile
# Multi-layer cache-optimised, non-root, health-checked
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# Build arguments for versioning (injected by CI pipeline)
ARG APP_VERSION=3.2.4
ARG BUILD_DATE
ARG GIT_COMMIT

# OCI image labels
LABEL org.opencontainers.image.title="ACEest Fitness & Gym"
LABEL org.opencontainers.image.version="${APP_VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${GIT_COMMIT}"
LABEL org.opencontainers.image.description="Fitness & Gym management REST API"

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000 \
    FLASK_DEBUG=false \
    DATABASE_URL=/data/aceest_fitness.db

# Create non-root user and data directory
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --shell /bin/bash --create-home appuser \
    && mkdir -p /data \
    && chown appuser:appgroup /data \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Layer 1: Install dependencies (cached unless requirements.txt changes) ───
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Layer 2: Copy application source ────────────────────────────────────────
COPY app.py .
COPY tests/ ./tests/

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root
USER appuser

EXPOSE 5000

# Production-grade health check
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=15s \
            --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Use gunicorn for production (Flask dev server for local testing)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "app:app"]
