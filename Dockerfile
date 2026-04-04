# ─────────────────────────────────────────────────────────────────────────────
# ACEest Fitness & Gym — Production Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
# Design goals:
#   • Minimal attack surface  → python:3.11-slim base image
#   • Layer-cache efficiency  → copy requirements first, code second
#   • Non-root execution      → dedicated system user (appuser)
#   • Built-in health probe   → Docker HEALTHCHECK via /api/health
#   • No dev artefacts        → .dockerignore excludes tests, .git, __pycache__
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── OS-level hygiene ──────────────────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# ── Non-root user (security best practice) ───────────────────────────────────
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --no-create-home appuser

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Dependencies (cached layer — only invalidated when requirements.txt changes) ─
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY app.py .
COPY tests/ ./tests/

# ── Ownership & permissions ───────────────────────────────────────────────────
RUN chown -R appuser:appgroup /app

# ── Switch to non-root user ───────────────────────────────────────────────────
USER appuser

# ── Runtime configuration ─────────────────────────────────────────────────────
ENV FLASK_ENV=production \
    PORT=5000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 5000

# ── Liveness / readiness probe ────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# ── Entrypoint ────────────────────────────────────────────────────────────────
CMD ["python", "app.py"]
