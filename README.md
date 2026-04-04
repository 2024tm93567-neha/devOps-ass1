# ACEest Fitness & Gym — DevOps CI/CD Project

> **A production-grade Flask REST API with automated CI/CD pipelines, containerisation, and comprehensive testing.**
>
> Built as part of the DevOps Assignment — demonstrating Version Control (Git), Containerisation (Docker), and Continuous Integration & Delivery (GitHub Actions + Jenkins).

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Application Architecture](#application-architecture)
3. [API Reference](#api-reference)
4. [Local Setup & Execution](#local-setup--execution)
5. [Running Tests Manually](#running-tests-manually)
6. [Docker Usage](#docker-usage)
7. [GitHub Actions CI/CD Pipeline](#github-actions-cicd-pipeline)
8. [Jenkins BUILD Integration](#jenkins-build-integration)
9. [Version History](#version-history)
10. [Project Structure](#project-structure)

---

## Project Overview

ACEest Fitness & Gym is a rapidly scaling startup. This repository contains the automated deployment workflow for their management system, transitioning from a tkinter desktop prototype through iterative development to a production-ready REST API with full CI/CD automation.

**Technology Stack**

| Layer | Technology |
|---|---|
| Web Framework | Flask 3.0 |
| Database | SQLite (via stdlib `sqlite3`) |
| Testing | Pytest + pytest-flask |
| Linting | flake8 |
| Containerisation | Docker (python:3.11-slim) |
| CI/CD (Cloud) | GitHub Actions |
| CI/CD (On-prem) | Jenkins Declarative Pipeline |

---

## Application Architecture

```
devOps-ass1
├── app.py                        ← Flask application (factory pattern)
│   ├── PROGRAMS                  ← Static fitness programme catalogue
│   ├── calculate_bmi()           ← Pure business-logic function
│   ├── calculate_calories()      ← Pure business-logic function
│   └── create_app(test_config)   ← Application factory
│
├── requirements.txt              ← Pinned production + dev dependencies
├── Dockerfile                    ← Optimised, non-root Docker image
├── .dockerignore                 ← Excludes .git, tests, __pycache__, etc.
├── Jenkinsfile                   ← Declarative Jenkins pipeline (6 stages)
│
├── .github/
│   └── workflows/
│       └── main.yml              ← GitHub Actions (4 jobs, 3 quality gates)
│
└── tests/
    ├── __init__.py
    ├── conftest.py               ← Session-scoped pytest fixtures
    └── test_app.py               ← 65+ test cases across 9 classes
```

### Design Decisions

- **Application Factory (`create_app`)** — the industry-standard Flask pattern that enables isolated test instances without side effects on the production database.
- **Pure Functions** — `calculate_bmi()` and `calculate_calories()` are module-level, stateless functions, making them directly unit-testable without spinning up an HTTP server.
- **SQLite WAL mode** — Write-Ahead Logging is enabled on every connection for better concurrent read performance.
- **Non-root Docker user** — The container runs as `appuser` (not `root`) to follow the principle of least privilege.

---

## API Reference

### Health & Meta

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service discovery — lists all endpoints |
| `GET` | `/api/health` | Liveness probe — returns `{"status":"healthy"}` |

### Programmes

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/programs` | List all training programmes |
| `GET` | `/api/programs/<name>` | Get full programme details by name |

Available programme names:
- `Fat Loss (FL) - 3 day`
- `Fat Loss (FL) - 5 day`
- `Muscle Gain (MG) - PPL`
- `Beginner (BG)`

### Calculators

| Method | Endpoint | Query Params | Description |
|---|---|---|---|
| `GET` | `/api/bmi` | `weight` (kg), `height` (cm) | BMI + category + risk note |
| `GET` | `/api/calories` | `weight` (kg), `program` (name) | Estimated daily kcal |

### Client Management

| Method | Endpoint | Body (JSON) | Description |
|---|---|---|---|
| `GET` | `/api/clients` | — | List all clients |
| `POST` | `/api/clients` | `name`*, `age`, `height`, `weight`, `program` | Create/update client |
| `GET` | `/api/clients/<name>` | — | Get client by name |
| `DELETE` | `/api/clients/<name>` | — | Delete client |

### Progress Tracking

| Method | Endpoint | Body (JSON) | Description |
|---|---|---|---|
| `POST` | `/api/clients/<name>/progress` | `week`*, `adherence`* (0–100) | Log weekly adherence |
| `GET` | `/api/clients/<name>/progress` | — | Full history + average adherence |

*\* Required field*

---

## Local Setup & Execution

Two options are available — **Option A** uses `requirements.txt` directly with Python, **Option B** uses Docker.

### Prerequisites

| Requirement | Option A (Python) | Option B (Docker) |
|---|---|---|
| Python 3.10+ | ✅ Required | ❌ Not needed |
| pip | ✅ Required | ❌ Not needed |
| Docker | ❌ Not needed | ✅ Required |

---

### Option A — Run with Python + requirements.txt

```bash
# 1. Clone the repository
git clone https://github.com/2024tm93567-neha/devOps-ass1.git

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install all dependencies from requirements.txt
pip install -r requirements.txt

# 4. Run the application
python app.py
# → Running on http://0.0.0.0:5000

# 5. Verify the app is running
curl http://localhost:5000/api/health
# → {"service":"aceest-fitness","status":"healthy"}

curl http://localhost:5000/api/programs
# → {"count":4,"programs":["Fat Loss (FL) - 3 day", ...]}
```

---

### Option B — Run with Docker

```bash
# 1. Clone the repository
git clone https://github.com/2024tm93567-neha/devOps-ass1.git

# 2. Build the Docker image
docker build -t aceest-fitness:latest .

# 3. Run the container
docker run -d \
  --name aceest-fitness \
  -p 5000:5000 \
  aceest-fitness:latest

# 4. Verify the container is running and healthy
docker ps
# STATUS should show: Up X seconds (healthy)

# 5. Test the application
curl http://localhost:5000/api/health
# → {"service":"aceest-fitness","status":"healthy"}

curl http://localhost:5000/api/programs
# → {"count":4,"programs":[...]}

# 6. Stop and remove when done
docker stop aceest-fitness && docker rm aceest-fitness
```

---

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `aceest_fitness.db` | Path to SQLite database file |
| `PORT` | `5000` | Port the application listens on |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode (`true`/`false`) |

---

## Running Tests Manually

### Option A — Tests with Python (requirements.txt)

```bash
# Activate virtual environment (if not already active)
source .venv/bin/activate

# Run the full test suite with verbose output
pytest tests/ -v

# Run a specific test class
pytest tests/test_app.py::TestBMIEndpoint -v
pytest tests/test_app.py::TestClientCRUD -v

# Run linter
flake8 app.py tests/ --max-line-length=100 --ignore=E501,W503,W504
# ✅ No output = lint passed
```

### Option B — Tests inside Docker container

```bash
# Run the full pytest suite inside the Docker container
docker run --rm aceest-fitness:latest \
  python -m pytest tests/ --verbose

# Expected output:
# platform linux -- Python 3.11.x
# 100 passed in 0.XXs
```

### Test Coverage Map

| Section | Class | Tests |
|---|---|---|
| A | `TestRootAndHealth` | 8 tests — service liveness & meta |
| B | `TestPrograms` | 12 tests — programme catalogue |
| C | `TestBMIEndpoint` | 11 tests — BMI calculator endpoint |
| D | `TestCalorieEndpoint` | 8 tests — calorie calculator endpoint |
| E | `TestClientCRUD` | 16 tests — full create/read/update/delete |
| F | `TestProgressTracking` | 12 tests — adherence logging |
| G | `TestCalculateBMI` | 12 tests — pure unit tests (no HTTP) |
| G | `TestCalculateCalories` | 8 tests — pure unit tests (no HTTP) |
| G | `TestProgramsData` | 6 tests — data integrity assertions |
| H | `TestEdgeCases` | 6 tests — error-handling & edge cases |

**Total: 100 tests**

---

## GitHub Actions CI/CD Pipeline

### Overview

The pipeline is defined in `.github/workflows/main.yml` and triggers on **every push** and **every pull request** to `main`.

```
Push / PR
    │
    ▼
┌──────────────────────────────────────────────┐
│  Job 1: Build & Lint                         │
│  • Set up Python 3.11                        │
│  • pip install -r requirements.txt           │
│  • flake8 lint gate (app.py + tests/)        │
│  • Import verification                       │
└───────────────────┬──────────────────────────┘
                    │ success
                    ▼
┌──────────────────────────────────────────────┐
│  Job 2: Docker Image Assembly                │
│  • docker build → aceest-fitness:<SHA>       │
│  • Verify HEALTHCHECK probe                  │
│  • Save image as Actions artifact            │
└───────────────────┬──────────────────────────┘
                    │ success
                    ▼
┌──────────────────────────────────────────────┐
│  Job 3: Automated Testing                    │
│  • Load saved Docker image                   │
│  • docker run → python -m pytest tests/ -v   │
│  • Upload JUnit XML test report              │
└───────────────────┬──────────────────────────┘
                    │ always
                    ▼
┌──────────────────────────────────────────────┐
│  Job 4: Pipeline Summary                     │
│  • Print commit SHA, branch, actor           │
└──────────────────────────────────────────────┘
```

### Key Features

- **Job dependencies** — downstream jobs run only after upstream jobs pass.
- **Artifact sharing** — the Docker image is saved as a compressed `.tar.gz` and passed between jobs, avoiding a re-build at test time.
- **JUnit XML upload** — test results are uploaded as an artifact for inspection.
- **Matrix-ready** — the `setup-python` step uses the cache strategy for fast dependency installation.

---

## Jenkins BUILD Integration

### Overview

The `Jenkinsfile` defines a **6-stage declarative pipeline** that Jenkins executes when it detects changes (via GitHub webhook or SCM polling).

```
┌──────────────────────────────────────────────────────┐
│  Stage 1: Checkout     — git pull from GitHub        │
│  Stage 2: Build Env    — python venv + pip install   │
│  Stage 3: Lint         — flake8 quality gate         │
│  Stage 4: Docker Build — docker build                │
│  Stage 5: Test         — pytest inside Docker        │
│  Stage 6: Smoke Test   — /api/health HTTP 200 check  │
└──────────────────────────────────────────────────────┘
```

### Jenkins Setup Steps

1. **Install Plugins** — *Pipeline*, *Git*, *Docker Pipeline*
2. **New Item** → *Pipeline* → name it `aceest-fitness`
3. **Pipeline Definition** → *Pipeline script from SCM*
4. **SCM** → Git → your repository URL
5. **Script Path** → `Jenkinsfile`
6. **Save → Build Now**

### Integration with GitHub Actions

Both systems enforce the **same quality gates** (lint → Docker build → pytest inside container), ensuring the codebase is consistently validated whether the build runs in the cloud (GitHub Actions) or on-premises (Jenkins).

| Quality Gate | GitHub Actions | Jenkins |
|---|---|---|
| Lint | ✅ flake8 | ✅ flake8 |
| Docker Build | ✅ docker build | ✅ docker build |
| Pytest in Docker | ✅ docker run pytest | ✅ docker run pytest |
| Health Probe | ✅ via HEALTHCHECK | ✅ curl smoke test |

---

## Version History

| Version | Key Changes |
|---|---|
| `v1.0` | tkinter prototype — programme display (workout/diet) |
| `v1.1` | Client profile inputs, calorie factor per programme |
| `v1.1.2` | Multi-client list, CSV export, embedded matplotlib charts |
| `v2.0.1` | SQLite persistence — save & load client profiles |
| `v2.1.2` | Weekly progress history with DB storage |
| `v2.2.1` | Adherence progress chart (matplotlib) |
| `v2.2.4` | Body metrics logging, workout tracking, BMI analytics |
| `v3.0.1` | Full client management — goals, analytics, status bar |
| `v3.1.2` | Login/auth, PDF export, AI-style programme generator |
| `v3.2.4` | **Production REST API** — Flask + SQLite + full CI/CD |

---

## Project Structure

```
devOps-aa1
├── .github/
│   └── workflows/
│       └── main.yml          ← GitHub Actions CI/CD (4 jobs)
├── tests/
│   ├── __init__.py
│   ├── conftest.py           ← pytest fixtures (session-scoped temp DB)
│   └── test_app.py           ← 98 tests across 9 test classes
├── .dockerignore             ← Exclude .git, venv, __pycache__, *.db
├── .gitignore
├── Dockerfile                ← python:3.11-slim, non-root, HEALTHCHECK
├── Jenkinsfile               ← 6-stage declarative pipeline
├── README.md                 ← This file
├── app.py                    ← Flask application (factory pattern)
└── requirements.txt          ← Flask, pytest, pytest-flask, flake8
```

---
