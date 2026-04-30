# ACEest Fitness & Gym — DevOps Assignment 2

> **Full CI/CD Pipeline** with Kubernetes, 5 Deployment Strategies, SonarQube, and Docker Hub versioning.

---

## Application Version History

All incremental versions of ACEest Fitness are in the `versions/` folder:

| File | Version | Key Feature Added |
|---|---|---|
| `ACEest_Fitness.py` | 3.2.4 | Production REST API — Flask + SQLite (same as `app.py`) |
| `Aceestver-3.2.4.py` | 3.2.4 | Production REST API |
| `Aceestver-3.1.2.py` | 3.1.2 | Login, PDF reports, AI-style program generator |
| `Aceestver-3.0.1.py` | 3.0.1 | Full client management with goals & analytics |
| `Aceestver-2.2.4.py` | 2.2.4 | Body metrics, workout logging, BMI analytics |
| `Aceestver-2.2.1.py` | 2.2.1 | Adherence chart (matplotlib) |
| `Aceestver-2.1.2.py` | 2.1.2 | Progress history (weekly adherence) |
| `Aceestver-2.0.1.py` | 2.0.1 | SQLite persistence, save/load clients |
| `Aceestver-1.1.2.py` | 1.1.2 | Multi-client list, CSV export, embedded charts |
| `Aceestver-1.1.py`   | 1.1   | Client profile + calorie factor |
| `Aceestver-1.0.py`   | 1.0   | Basic program display (tkinter prototype) |

The production deployment (`app.py`) is always the latest version: **v3.2.4 REST API**.

---

## Quick Start (Local Testing)

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | `brew install python` |
| Docker | 24+ | [docker.com](https://docker.com) |
| kubectl | 1.28+ | `brew install kubectl` |
| Minikube | 1.33+ | `brew install minikube` |
| sonar-scanner | 5+ | `brew install sonar-scanner` |

### 1. Run Flask API locally

```bash
# Create virtual environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start Flask
python app.py
# → http://localhost:5000/api/health
```

### 2. Run all 100 tests

```bash
source .venv/bin/activate
pytest tests/ -v --cov=app --cov-report=term-missing
```

### 3. Build & run with Docker

```bash
# Build
docker build -t nehartonpe/aceest-fitness:3.2.4 .

# Run
docker run -p 5000:5000 nehartonpe/aceest-fitness:3.2.4

# Test
curl http://localhost:5000/api/health
```

### 4. Build & run with Podman (rootless — no daemon required)

```bash
# Build using Containerfile (Podman default — identical OCI syntax)
podman build -f Containerfile -t nehaRTonpe/aceest-fitness:3.2.4 .

# Run (rootless — no sudo needed)
podman run -p 5000:5000 nehaRTonpe/aceest-fitness:3.2.4

# Test
curl http://localhost:5000/api/health

# Full build + test + push workflow
bash scripts/podman-build.sh 3.2.4 nehaRTonpe
```

> **Docker vs Podman**: Both produce identical OCI images. Jenkins auto-detects
> which engine is available (`command -v docker || podman`) and uses it.
> `Dockerfile` = used by Docker. `Containerfile` = used by Podman (same content).

### 5. Pull from Docker Hub

```bash
# Pull specific version
docker pull nehaRTonpe/aceest-fitness:3.2.4
podman pull docker.io/nehaRTonpe/aceest-fitness:3.2.4

# Pull latest
docker pull nehaRTonpe/aceest-fitness:latest
```

---

## Kubernetes Deployment — All 5 Strategies

### Start Minikube

```bash
minikube start --driver=docker --cpus=2 --memory=4g
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
```

### Strategy 1 — Rolling Update (default)

```bash
bash scripts/deploy.sh rolling nehaRTonpe/aceest-fitness:3.2.4

# Watch rollout
kubectl rollout status deployment/aceest-fitness-rolling -n aceest-fitness

# Rollback
bash scripts/rollback.sh aceest-fitness rolling
```

### Strategy 2 — Blue-Green

```bash
bash scripts/deploy.sh blue-green nehaRTonpe/aceest-fitness:3.2.4

# Manual traffic switch to Green:
kubectl patch service aceest-fitness-svc \
  -n aceest-fitness \
  -p '{"spec":{"selector":{"app":"aceest-fitness","slot":"green"}}}'

# Rollback to Blue:
kubectl patch service aceest-fitness-svc \
  -n aceest-fitness \
  -p '{"spec":{"selector":{"app":"aceest-fitness","slot":"blue"}}}'
```

### Strategy 3 — Canary (10% traffic)

```bash
bash scripts/deploy.sh canary nehaRTonpe/aceest-fitness:3.2.5

# Monitor → promote canary to 100%:
kubectl scale deployment/aceest-fitness-canary --replicas=9 -n aceest-fitness
kubectl scale deployment/aceest-fitness-stable --replicas=0 -n aceest-fitness

# Rollback (eliminate canary):
bash scripts/rollback.sh aceest-fitness canary
```

### Strategy 4 — Shadow

```bash
bash scripts/deploy.sh shadow nehaRTonpe/aceest-fitness:3.2.5

# Shadow receives mirrored traffic — responses discarded
# Monitor shadow logs for errors:
kubectl logs -l track=shadow -n aceest-fitness --follow

# Rollback (scale shadow down):
bash scripts/rollback.sh aceest-fitness shadow
```

### Strategy 5 — A/B Testing

```bash
bash scripts/deploy.sh ab-testing nehaRTonpe/aceest-fitness:3.2.5

# Test Variant A (control — default):
curl http://$(minikube ip):30080/api/health

# Test Variant B (experiment — cookie-based routing):
curl -H "Cookie: ab_group=b" http://$(minikube ip):30080/api/health

# Rollback Variant B:
bash scripts/rollback.sh aceest-fitness ab-testing
```

---

## CI/CD Pipeline

### Jenkins Setup

1. Install Jenkins with Docker + Python3 on the build agent
2. Configure credentials:
   - `dockerhub-credentials` → Docker Hub username/password
   - `kubeconfig` → K8s cluster kubeconfig file
   - `sonar-token` → SonarQube auth token
3. Create a Pipeline job pointing to this repository
4. Jenkinsfile auto-detected from repo root

**Pipeline Stages:**

```
Checkout → Build Env → Lint → SonarQube → Docker Build
  → Test → Smoke Test → Docker Push → K8s Namespace → Deploy → Verify
```

### GitHub Actions

Runs on every push. Requires secrets:
- `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `SONAR_TOKEN`, `SONAR_HOST_URL`

---

## SonarQube

```bash
# Run locally (SonarQube server must be running at localhost:9000)
sonar-scanner \
  -Dsonar.login=<your-token> \
  -Dsonar.host.url=http://localhost:9000
```

Config file: `sonar-project.properties`

---

## Docker Hub — All Version Tags

| Tag | Description |
|---|---|
| `3.2.4` | Current production REST API |
| `3.1.2` | Login + PDF reports |
| `3.0.1` | Full client management |
| `2.2.4` | Body metrics + BMI analytics |
| `2.2.1` | Adherence charts |
| `2.1.2` | Progress history |
| `2.0.1` | SQLite persistence |
| `1.1.2` | Multi-client + CSV export |
| `1.1` | Client profile + calorie factor |
| `1.0` | Basic program display |
| `latest` | Alias for `3.2.4` |

Push all versions: `bash scripts/push-versions.sh`

---

## Project Structure

```
devOps-ass2/
├── app.py                          # Flask REST API v3.2.4 (application factory)
├── requirements.txt                # Pinned dependencies
├── Dockerfile                      # Non-root, health-checked, gunicorn
├── Jenkinsfile                     # Full CI/CD declarative pipeline (9 stages)
├── sonar-project.properties        # SonarQube configuration
├── k8s/
│   ├── namespace.yaml              # aceest-fitness namespace
│   ├── configmap.yaml              # Shared env vars (DRY)
│   ├── blue-green/
│   │   ├── deployment-blue.yaml    # Stable production
│   │   ├── deployment-green.yaml   # Candidate version
│   │   └── service.yaml            # Traffic switch via selector patch
│   ├── canary/
│   │   ├── deployment-stable.yaml  # 9 replicas → 90% traffic
│   │   ├── deployment-canary.yaml  # 1 replica  → 10% traffic
│   │   └── service.yaml
│   ├── rolling/
│   │   └── deployment.yaml         # maxSurge=1, maxUnavailable=0
│   ├── shadow/
│   │   ├── deployment-prod.yaml    # Real traffic
│   │   ├── deployment-shadow.yaml  # Mirrored traffic (discarded responses)
│   │   └── service.yaml            # + Istio VirtualService template
│   └── ab-testing/
│       ├── deployment-a.yaml       # Variant A (control)
│       ├── deployment-b.yaml       # Variant B (experiment)
│       └── service.yaml            # + Nginx Ingress cookie routing
├── scripts/
│   ├── deploy.sh                   # Unified deploy (all 5 strategies)
│   ├── rollback.sh                 # Strategy-specific rollback
│   └── push-versions.sh            # Docker Hub multi-version push
├── versions/
│   ├── ACEest_Fitness.py           # Production app alias (v3.2.4)
│   ├── Aceestver-1.0.py            # tkinter prototype
│   ├── Aceestver-1.1.py            # Client profile + calorie factor
│   ├── Aceestver-1.1.2.py          # Multi-client + CSV export
│   ├── Aceestver-2.0.1.py          # SQLite persistence
│   ├── Aceestver-2.1.2.py          # Progress history
│   ├── Aceestver-2.2.1.py          # Adherence charts
│   ├── Aceestver-2.2.4.py          # BMI analytics
│   ├── Aceestver-3.0.1.py          # Full client management
│   ├── Aceestver-3.1.2.py          # Login + PDF reports
│   └── Aceestver-3.2.4.py          # Production REST API
├── tests/
│   ├── conftest.py                 # Fixtures: temp DB, test client
│   └── test_app.py                 # 100 tests across 9 classes
├── .github/
│   └── workflows/
│       └── main.yml                # GitHub Actions CI/CD
└── reports/
    └── cicd-report.md              # 2-3 page CI/CD architecture report
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API info + available endpoints |
| GET | `/api/health` | Health probe (used by K8s liveness/readiness) |
| GET | `/api/programs` | List all fitness programs |
| GET | `/api/programs/<name>` | Program details |
| GET | `/api/bmi?weight=&height=` | BMI calculation + category |
| GET | `/api/calories?weight=&program=` | Daily calorie estimate |
| GET | `/api/clients` | List all clients |
| POST | `/api/clients` | Create/update client |
| GET | `/api/clients/<name>` | Get single client |
| DELETE | `/api/clients/<name>` | Delete client |
| POST | `/api/clients/<name>/progress` | Log weekly adherence |
| GET | `/api/clients/<name>/progress` | Get progress history |

---
