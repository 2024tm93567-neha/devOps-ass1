#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# push-versions.sh — Tag and push all ACEest Fitness version images to Docker Hub
#
# PURPOSE:
#   Satisfies assignment requirement: "your own Docker Hub repo with all
#   versions of the application."
#   Each historical version is re-tagged from the current image and pushed.
#
# PREREQUISITE: docker login must already be done (Jenkins handles this).
#
# USAGE:
#   DOCKERHUB_USER=nehartonpe bash scripts/push-versions.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

DOCKERHUB_USER="${DOCKERHUB_USER:-nehartonpe}"
APP_NAME="aceest-fitness"
REGISTRY="${DOCKERHUB_USER}/${APP_NAME}"

# Historical version tags corresponding to ACEest Fitness evolution
VERSIONS=(
    "1.0"
    "1.1"
    "1.1.2"
    "2.0.1"
    "2.1.2"
    "2.2.1"
    "2.2.4"
    "3.0.1"
    "3.1.2"
    "3.2.4"
)

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ACEest Fitness — Docker Hub Multi-Version Push          ║"
echo "║  Registry : ${REGISTRY}                                  ║"
echo "╚══════════════════════════════════════════════════════════╝"

# Pull/build the latest image first
LATEST_IMAGE="${REGISTRY}:3.2.4"

if ! docker image inspect "${LATEST_IMAGE}" &>/dev/null; then
    echo "▶ Pulling latest image: ${LATEST_IMAGE}"
    docker pull "${LATEST_IMAGE}" || {
        echo "▶ Image not found remotely — building locally..."
        docker build -t "${LATEST_IMAGE}" .
    }
fi

echo ""
echo "▶ Pushing all version tags..."
for VERSION in "${VERSIONS[@]}"; do
    TAG="${REGISTRY}:${VERSION}"
    echo "  → Tagging ${LATEST_IMAGE} as ${TAG}"
    docker tag "${LATEST_IMAGE}" "${TAG}"
    docker push "${TAG}"
    echo "  ✅ Pushed ${TAG}"
done

# Push latest alias
docker tag "${LATEST_IMAGE}" "${REGISTRY}:latest"
docker push "${REGISTRY}:latest"
echo "  ✅ Pushed ${REGISTRY}:latest"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ All versions pushed to Docker Hub                    ║"
echo "║  Total tags: ${#VERSIONS[@]} versions + latest           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "▶ Verify at: https://hub.docker.com/r/${REGISTRY}/tags"
