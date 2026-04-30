#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# podman-build.sh — Build, test, and push ACEest Fitness image using Podman
#
# WHY PODMAN:
#   Podman is a daemonless, rootless OCI container engine — no Docker daemon
#   required. It uses the same Dockerfile/Containerfile syntax and produces
#   OCI-compliant images fully compatible with Kubernetes and Docker Hub.
#   Preferred in rootless CI environments (no /var/run/docker.sock needed).
#
# USAGE:
#   bash scripts/podman-build.sh [version] [dockerhub-user]
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

APP_VERSION="${1:-3.2.4}"
DOCKERHUB_USER="${2:-nehartonpe}"
APP_NAME="aceest-fitness"
REGISTRY="docker.io/${DOCKERHUB_USER}/${APP_NAME}"
IMAGE_TAG="${REGISTRY}:${APP_VERSION}"
IMAGE_LATEST="${REGISTRY}:latest"
BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ACEest Fitness — Podman Build & Push                    ║"
echo "║  Version : ${APP_VERSION}                                ║"
echo "║  Image   : ${IMAGE_TAG}                                  ║"
echo "╚══════════════════════════════════════════════════════════╝"

# ── 1. Build image with Podman (rootless — no daemon required) ───────────────
echo ""
echo "▶ Building OCI image with Podman (rootless)..."
podman build \
    --file Containerfile \
    --build-arg APP_VERSION="${APP_VERSION}" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg GIT_COMMIT="${GIT_COMMIT}" \
    --tag "${IMAGE_TAG}" \
    --tag "${IMAGE_LATEST}" \
    --label "org.opencontainers.image.created=${BUILD_DATE}" \
    --label "org.opencontainers.image.revision=${GIT_COMMIT}" \
    .

echo "✅ Podman build complete."
podman images "${REGISTRY}"

# ── 2. Run tests inside Podman container ─────────────────────────────────────
echo ""
echo "▶ Running pytest inside Podman container..."
podman run --rm \
    --name "${APP_NAME}-test-podman" \
    --env DATABASE_URL=/tmp/test_aceest.db \
    "${IMAGE_TAG}" \
    python -m pytest tests/ \
        --verbose \
        --tb=short \
        --color=no \
        -p no:cacheprovider

echo "✅ All tests passed inside Podman container."

# ── 3. Smoke test ─────────────────────────────────────────────────────────────
echo ""
echo "▶ Running smoke test..."
podman run -d \
    --name "${APP_NAME}-smoke-podman" \
    -p 5099:5000 \
    --env DATABASE_URL=/tmp/smoke.db \
    "${IMAGE_TAG}"

sleep 8

STATUS=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:5099/api/health || echo "000")
podman stop "${APP_NAME}-smoke-podman" 2>/dev/null || true
podman rm   "${APP_NAME}-smoke-podman" 2>/dev/null || true

if [ "${STATUS}" != "200" ]; then
    echo "❌ Smoke test failed — HTTP ${STATUS}"
    exit 1
fi
echo "✅ Smoke test passed — HTTP ${STATUS}"

# ── 4. Push to Docker Hub via Podman ─────────────────────────────────────────
echo ""
echo "▶ Logging in to Docker Hub..."
podman login docker.io \
    --username "${DOCKERHUB_USER}" \
    --get-login 2>/dev/null || \
podman login docker.io \
    --username "${DOCKERHUB_USER}"

echo "▶ Pushing ${IMAGE_TAG}..."
podman push "${IMAGE_TAG}"
podman push "${IMAGE_LATEST}"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ Podman build + push complete                         ║"
echo "║  Image : ${IMAGE_TAG}"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "▶ Verify: https://hub.docker.com/r/${DOCKERHUB_USER}/${APP_NAME}/tags"

# ── 5. Podman-specific: export image as OCI tar (portable) ───────────────────
echo ""
echo "▶ Exporting OCI image archive (podman save)..."
mkdir -p build-artifacts
podman save \
    --format oci-archive \
    --output "build-artifacts/${APP_NAME}-${APP_VERSION}-oci.tar" \
    "${IMAGE_TAG}"
echo "✅ OCI archive saved: build-artifacts/${APP_NAME}-${APP_VERSION}-oci.tar"
echo "   Load on any OCI-compatible runtime:"
echo "   podman load -i build-artifacts/${APP_NAME}-${APP_VERSION}-oci.tar"
echo "   docker load < build-artifacts/${APP_NAME}-${APP_VERSION}-oci.tar"
