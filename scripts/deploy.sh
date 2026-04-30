#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy.sh — Unified deployment script for all 5 K8s strategies
#
# USAGE:
#   bash scripts/deploy.sh <strategy> <image-tag>
#
# STRATEGIES:
#   rolling    → Rolling update (default)
#   blue-green → Blue-Green instant traffic switch
#   canary     → Canary release (10% / 90% replica split)
#   shadow     → Shadow / mirroring deployment
#   ab-testing → A/B testing with cookie-based routing
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

STRATEGY="${1:-rolling}"
IMAGE_TAG="${2:-nehaRTonpe/aceest-fitness:3.2.4}"
NAMESPACE="aceest-fitness"
APP_NAME="aceest-fitness"
K8S_DIR="$(dirname "$0")/../k8s"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  ACEest Fitness — Kubernetes Deploy                  ║"
echo "║  Strategy : ${STRATEGY}"
echo "║  Image    : ${IMAGE_TAG}"
echo "║  Namespace: ${NAMESPACE}"
echo "╚══════════════════════════════════════════════════════╝"

# ── Ensure namespace exists ──────────────────────────────────────────────────
kubectl apply -f "${K8S_DIR}/namespace.yaml"
kubectl apply -f "${K8S_DIR}/configmap.yaml"

deploy_rolling() {
    echo "▶ Applying Rolling Update deployment..."
    kubectl apply -f "${K8S_DIR}/rolling/deployment.yaml"
    kubectl set image deployment/${APP_NAME}-rolling \
        ${APP_NAME}="${IMAGE_TAG}" \
        -n "${NAMESPACE}"
    kubectl rollout status deployment/${APP_NAME}-rolling \
        -n "${NAMESPACE}" --timeout=120s
    echo "✅ Rolling update complete."
}

deploy_blue_green() {
    echo "▶ Applying Blue-Green deployment..."
    kubectl apply -f "${K8S_DIR}/blue-green/deployment-blue.yaml"
    kubectl apply -f "${K8S_DIR}/blue-green/deployment-green.yaml"
    kubectl apply -f "${K8S_DIR}/blue-green/service.yaml"

    # Update green with the new image
    kubectl set image deployment/${APP_NAME}-green \
        ${APP_NAME}="${IMAGE_TAG}" \
        -n "${NAMESPACE}"

    echo "▶ Waiting for Green deployment to be ready..."
    kubectl rollout status deployment/${APP_NAME}-green \
        -n "${NAMESPACE}" --timeout=120s

    echo "▶ Switching traffic to Green..."
    kubectl patch service aceest-fitness-svc \
        -n "${NAMESPACE}" \
        -p '{"spec":{"selector":{"app":"aceest-fitness","slot":"green"}}}'

    echo "✅ Blue-Green deployment complete — traffic now on GREEN."
    echo "   To rollback: kubectl patch service aceest-fitness-svc -n ${NAMESPACE} -p '{\"spec\":{\"selector\":{\"app\":\"aceest-fitness\",\"slot\":\"blue\"}}}'"
}

deploy_canary() {
    echo "▶ Applying Canary deployment (10% traffic to canary)..."
    kubectl apply -f "${K8S_DIR}/canary/deployment-stable.yaml"
    kubectl apply -f "${K8S_DIR}/canary/deployment-canary.yaml"
    kubectl apply -f "${K8S_DIR}/canary/service.yaml"

    # Update canary with new image
    kubectl set image deployment/${APP_NAME}-canary \
        ${APP_NAME}="${IMAGE_TAG}" \
        -n "${NAMESPACE}"

    kubectl rollout status deployment/${APP_NAME}-canary \
        -n "${NAMESPACE}" --timeout=120s

    echo "✅ Canary deployed — 1 canary replica of ${IMAGE_TAG} serving ~10% traffic."
    echo "   Monitor → then promote: kubectl scale deployment/${APP_NAME}-canary --replicas=9 -n ${NAMESPACE}"
}

deploy_shadow() {
    echo "▶ Applying Shadow deployment..."
    kubectl apply -f "${K8S_DIR}/shadow/deployment-prod.yaml"
    kubectl apply -f "${K8S_DIR}/shadow/deployment-shadow.yaml"
    kubectl apply -f "${K8S_DIR}/shadow/service.yaml"

    # Update shadow with new image (prod stays on stable)
    kubectl set image deployment/${APP_NAME}-shadow \
        ${APP_NAME}="${IMAGE_TAG}" \
        -n "${NAMESPACE}"

    kubectl rollout status deployment/${APP_NAME}-shadow \
        -n "${NAMESPACE}" --timeout=120s

    echo "✅ Shadow deployment active — mirroring production traffic to shadow pods."
    echo "   Shadow responses are discarded; monitor shadow logs for errors."
}

deploy_ab_testing() {
    echo "▶ Applying A/B Testing deployment..."
    kubectl apply -f "${K8S_DIR}/ab-testing/deployment-a.yaml"
    kubectl apply -f "${K8S_DIR}/ab-testing/deployment-b.yaml"
    kubectl apply -f "${K8S_DIR}/ab-testing/service.yaml"

    # Update variant-b with the new image
    kubectl set image deployment/${APP_NAME}-variant-b \
        ${APP_NAME}="${IMAGE_TAG}" \
        -n "${NAMESPACE}"

    kubectl rollout status deployment/${APP_NAME}-variant-b \
        -n "${NAMESPACE}" --timeout=120s

    echo "✅ A/B testing deployed."
    echo "   Variant A (control) → default traffic"
    echo "   Variant B (experiment) → users with cookie 'ab_group=b'"
}

# ── Route to correct strategy ────────────────────────────────────────────────
case "${STRATEGY}" in
    rolling)    deploy_rolling    ;;
    blue-green) deploy_blue_green ;;
    canary)     deploy_canary     ;;
    shadow)     deploy_shadow     ;;
    ab-testing) deploy_ab_testing ;;
    *)
        echo "❌ Unknown strategy: ${STRATEGY}"
        echo "   Valid options: rolling | blue-green | canary | shadow | ab-testing"
        exit 1
        ;;
esac

echo ""
echo "▶ Current pods in namespace ${NAMESPACE}:"
kubectl get pods -n "${NAMESPACE}" -o wide
echo ""
echo "▶ Current services:"
kubectl get svc -n "${NAMESPACE}"
