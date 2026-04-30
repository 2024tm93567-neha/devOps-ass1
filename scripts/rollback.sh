#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# rollback.sh — Rollback to previous stable deployment
#
# USAGE:
#   bash scripts/rollback.sh [namespace] [strategy]
#
# EXAMPLES:
#   bash scripts/rollback.sh aceest-fitness rolling
#   bash scripts/rollback.sh aceest-fitness blue-green
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

NAMESPACE="${1:-aceest-fitness}"
STRATEGY="${2:-rolling}"
APP_NAME="aceest-fitness"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  ACEest Fitness — ROLLBACK initiated                 ║"
echo "║  Namespace: ${NAMESPACE} | Strategy: ${STRATEGY}    ║"
echo "╚══════════════════════════════════════════════════════╝"

rollback_rolling() {
    echo "▶ Rolling back Rolling deployment..."
    kubectl rollout undo deployment/${APP_NAME}-rolling -n "${NAMESPACE}"
    kubectl rollout status deployment/${APP_NAME}-rolling \
        -n "${NAMESPACE}" --timeout=90s
    echo "✅ Rolling rollback complete."
}

rollback_blue_green() {
    echo "▶ Switching traffic back to BLUE (stable)..."
    kubectl patch service aceest-fitness-svc \
        -n "${NAMESPACE}" \
        -p '{"spec":{"selector":{"app":"aceest-fitness","slot":"blue"}}}'
    echo "✅ Blue-Green rollback complete — traffic restored to BLUE."
}

rollback_canary() {
    echo "▶ Scaling down canary to 0 replicas..."
    kubectl scale deployment/${APP_NAME}-canary \
        --replicas=0 -n "${NAMESPACE}"
    echo "✅ Canary rollback complete — 100% traffic on stable."
}

rollback_shadow() {
    echo "▶ Scaling down shadow deployment..."
    kubectl scale deployment/${APP_NAME}-shadow \
        --replicas=0 -n "${NAMESPACE}"
    echo "✅ Shadow deployment scaled down."
}

rollback_ab_testing() {
    echo "▶ Rolling back Variant B..."
    kubectl rollout undo deployment/${APP_NAME}-variant-b -n "${NAMESPACE}"
    echo "✅ A/B rollback complete — Variant B reverted."
}

case "${STRATEGY}" in
    rolling)    rollback_rolling    ;;
    blue-green) rollback_blue_green ;;
    canary)     rollback_canary     ;;
    shadow)     rollback_shadow     ;;
    ab-testing) rollback_ab_testing ;;
    *)
        echo "▶ Strategy not specified — attempting generic rollback..."
        kubectl rollout undo deployment/${APP_NAME} -n "${NAMESPACE}" 2>/dev/null || true
        kubectl rollout undo deployment/${APP_NAME}-rolling -n "${NAMESPACE}" 2>/dev/null || true
        ;;
esac

echo ""
echo "▶ Post-rollback pod state:"
kubectl get pods -n "${NAMESPACE}" -o wide 2>/dev/null || true
