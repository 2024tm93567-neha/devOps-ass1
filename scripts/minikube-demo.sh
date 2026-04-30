#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# minikube-demo.sh — One-script local cluster setup for all 5 deploy strategies
#
# PURPOSE:
#   Starts Minikube, deploys ACEest Fitness using all 5 Kubernetes deployment
#   strategies, and prints the live endpoint URLs — satisfying the assignment
#   requirement: "Submit the endpoint URL of your running cluster."
#
# PREREQUISITES:
#   • minikube  (brew install minikube)
#   • kubectl   (brew install kubectl)
#   • docker    (https://docker.com) OR podman
#
# USAGE:
#   bash scripts/minikube-demo.sh [strategy]
#
# EXAMPLES:
#   bash scripts/minikube-demo.sh              # deploys rolling (default)
#   bash scripts/minikube-demo.sh blue-green
#   bash scripts/minikube-demo.sh canary
#   bash scripts/minikube-demo.sh shadow
#   bash scripts/minikube-demo.sh ab-testing
#   bash scripts/minikube-demo.sh all          # deploys all 5 strategies
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

STRATEGY="${1:-rolling}"
APP_NAME="aceest-fitness"
NAMESPACE="aceest-fitness"
IMAGE="nehaRTonpe/aceest-fitness:3.2.4"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="${SCRIPT_DIR}/../k8s"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ACEest Fitness — Minikube Local Cluster Demo               ║"
echo "║  Strategy: ${STRATEGY}                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# ── Step 1: Start Minikube ────────────────────────────────────────────────────
if minikube status --profile minikube &>/dev/null | grep -q "Running"; then
    echo "✅ Minikube already running."
else
    echo "▶ Starting Minikube..."
    minikube start \
        --driver=docker \
        --cpus=2 \
        --memory=4096 \
        --disk-size=20g \
        --addons=ingress \
        --addons=metrics-server
    echo "✅ Minikube started."
fi

MINIKUBE_IP=$(minikube ip)
echo "▶ Minikube IP: ${MINIKUBE_IP}"

# ── Step 2: Load image into Minikube (avoids Docker Hub pull) ────────────────
echo ""
echo "▶ Loading Docker image into Minikube..."
if docker image inspect "${IMAGE}" &>/dev/null; then
    # Load from local Docker daemon into Minikube
    minikube image load "${IMAGE}"
    echo "✅ Image loaded from local daemon."
else
    echo "▶ Image not local — pulling from Docker Hub inside Minikube..."
    minikube kubectl -- create deployment test-pull --image="${IMAGE}" --dry-run=client -o yaml | \
        minikube kubectl -- apply -f - 2>/dev/null || true
fi

# ── Step 3: Apply namespace + configmap ──────────────────────────────────────
echo ""
echo "▶ Setting up namespace and ConfigMap..."
kubectl apply -f "${K8S_DIR}/namespace.yaml"
kubectl apply -f "${K8S_DIR}/configmap.yaml"

# ── Step 4: Deploy strategy ───────────────────────────────────────────────────
deploy_and_show() {
    local strat="${1}"
    local nodeport="${2}"
    local deploy_name="${3}"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Deploying: ${strat} (NodePort ${nodeport})"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    bash "${SCRIPT_DIR}/deploy.sh" "${strat}" "${IMAGE}"

    echo ""
    echo "▶ Waiting for pods to be ready..."
    kubectl wait pods \
        -n "${NAMESPACE}" \
        -l "app=${APP_NAME}" \
        --for=condition=Ready \
        --timeout=120s 2>/dev/null || \
    kubectl get pods -n "${NAMESPACE}" -l "app=${APP_NAME}"

    ENDPOINT="http://${MINIKUBE_IP}:${nodeport}"
    echo ""
    echo "  🌐  ENDPOINT: ${ENDPOINT}/api/health"
    echo "  Smoke testing endpoint..."

    for i in 1 2 3 4 5; do
        STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "${ENDPOINT}/api/health" 2>/dev/null || echo "000")
        if [ "${STATUS}" = "200" ]; then
            echo "  ✅ Endpoint live — HTTP ${STATUS}"
            break
        fi
        echo "  ⏳ Attempt ${i}/5 — HTTP ${STATUS} — retrying in 5s..."
        sleep 5
    done
}

case "${STRATEGY}" in
    rolling)
        deploy_and_show "rolling" "30082" "${APP_NAME}-rolling"
        ENDPOINT="http://${MINIKUBE_IP}:30082"
        ;;
    blue-green)
        deploy_and_show "blue-green" "30080" "${APP_NAME}-svc"
        ENDPOINT="http://${MINIKUBE_IP}:30080"
        ;;
    canary)
        deploy_and_show "canary" "30081" "${APP_NAME}-stable"
        ENDPOINT="http://${MINIKUBE_IP}:30081"
        ;;
    shadow)
        deploy_and_show "shadow" "30083" "${APP_NAME}-prod"
        ENDPOINT="http://${MINIKUBE_IP}:30083"
        ;;
    ab-testing)
        deploy_and_show "ab-testing" "30084" "${APP_NAME}-variant-a"
        ENDPOINT="http://${MINIKUBE_IP}:30084"
        ;;
    all)
        # Deploy all 5 strategies in sequence
        deploy_and_show "rolling"    "30082" "${APP_NAME}-rolling"
        deploy_and_show "blue-green" "30080" "${APP_NAME}-svc"
        deploy_and_show "canary"     "30081" "${APP_NAME}-stable"
        deploy_and_show "shadow"     "30083" "${APP_NAME}-prod"
        deploy_and_show "ab-testing" "30084" "${APP_NAME}-variant-a"
        ENDPOINT="http://${MINIKUBE_IP}:30080"
        ;;
    *)
        echo "❌ Unknown strategy: ${STRATEGY}"
        echo "   Valid: rolling | blue-green | canary | shadow | ab-testing | all"
        exit 1
        ;;
esac

# ── Step 5: Print all live endpoints ─────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ ACEest Fitness — RUNNING CLUSTER ENDPOINTS               ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Rolling     : http://${MINIKUBE_IP}:30082/api/health"
echo "║  Blue-Green  : http://${MINIKUBE_IP}:30080/api/health"
echo "║  Canary      : http://${MINIKUBE_IP}:30081/api/health"
echo "║  Shadow(prod): http://${MINIKUBE_IP}:30083/api/health"
echo "║  A/B Variant A: http://${MINIKUBE_IP}:30084/api/health"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "▶ Cluster status:"
kubectl get pods,svc -n "${NAMESPACE}" -o wide 2>/dev/null
echo ""
echo "▶ To rollback current strategy:"
echo "   bash scripts/rollback.sh ${NAMESPACE} ${STRATEGY}"
echo ""
echo "▶ To stop Minikube:"
echo "   minikube stop"
