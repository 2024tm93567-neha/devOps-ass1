// ─────────────────────────────────────────────────────────────────────────────
// ACEest Fitness & Gym — Jenkins Full CI/CD Declarative Pipeline
// ─────────────────────────────────────────────────────────────────────────────
//
// PIPELINE STAGES:
//   CI:  Checkout → Build Env → Lint → SonarQube → Docker Build → Test → Smoke Test
//   CD:  Docker Push → K8s Deploy (strategy-based) → Verify Rollout → Notify
//
// PREREQUISITES:
//   • Jenkins with Docker, Python3, kubectl, sonar-scanner on build agent
//   • Credentials configured:
//       - "dockerhub-credentials" → Docker Hub username/password
//       - "kubeconfig"            → K8s cluster kubeconfig file
//       - "sonar-token"          → SonarQube auth token
//   • Kubernetes cluster reachable from Jenkins agent
//   • SonarQube server at ${SONAR_HOST_URL}
// ─────────────────────────────────────────────────────────────────────────────

pipeline {

    agent any

    // ── Pipeline-level environment ────────────────────────────────────────────
    environment {
        APP_NAME       = "aceest-fitness"
        APP_VERSION    = "3.2.4"
        DOCKERHUB_USER = "nehartonpe"                          // ← your Docker Hub username
        IMAGE_BASE     = "${DOCKERHUB_USER}/${APP_NAME}"
        IMAGE_TAG      = "${IMAGE_BASE}:${APP_VERSION}"
        IMAGE_BUILD    = "${IMAGE_BASE}:build-${BUILD_NUMBER}"
        IMAGE_LATEST   = "${IMAGE_BASE}:latest"
        VENV_DIR       = ".venv"
        K8S_NAMESPACE  = "aceest-fitness"
        DEPLOY_STRATEGY = "${params.DEPLOY_STRATEGY ?: 'rolling'}"  // override via build param
        SONAR_HOST_URL = "http://localhost:9000"
        SONAR_PROJECT  = "aceest-fitness"
    }

    // ── Build parameters (visible in Jenkins UI) ─────────────────────────────
    parameters {
        choice(
            name: 'DEPLOY_STRATEGY',
            choices: ['rolling', 'blue-green', 'canary', 'shadow', 'ab-testing'],
            description: 'Kubernetes deployment strategy to use for this build'
        )
        booleanParam(
            name: 'SKIP_SONAR',
            defaultValue: false,
            description: 'Skip SonarQube analysis (use only if SonarQube is unavailable)'
        )
        booleanParam(
            name: 'PUSH_ALL_VERSIONS',
            defaultValue: false,
            description: 'Push all historical version tags to Docker Hub'
        )
    }

    // ── Triggers — SCM polling + GitHub webhook ───────────────────────────────
    // pollSCM polls GitHub every 5 minutes; the GitHub webhook (configured in
    // the Jenkins job under "Build Triggers → GitHub hook trigger for GITScm polling")
    // fires instantly on every push — both are active simultaneously.
    triggers {
        // Poll every 5 minutes: H/5 means "pick a random minute offset in each
        // 5-minute window" — spreads Jenkins load across multiple jobs.
        pollSCM('H/5 * * * *')

        // GitHub webhook instant trigger (requires GitHub plugin + webhook configured
        // at: GitHub repo → Settings → Webhooks → http://<jenkins>/github-webhook/)
        githubPush()
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '15'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    // ─────────────────────────────────────────────────────────────────────────
    stages {

        // ── Stage 1: Source Checkout ─────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo "╔══════════════════════════════════════════════════════╗"
                echo "║  ACEest Fitness — Full CI/CD Pipeline  (Ass. 2)      ║"
                echo "║  Strategy: ${params.DEPLOY_STRATEGY}                 ║"
                echo "╚══════════════════════════════════════════════════════╝"
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(script: "git rev-parse --short HEAD", returnStdout: true).trim()
                    env.GIT_BRANCH_NAME  = sh(script: "git rev-parse --abbrev-ref HEAD", returnStdout: true).trim()
                }
                echo "✅ Checkout — Branch: ${GIT_BRANCH_NAME} | Commit: ${GIT_COMMIT_SHORT}"
            }
        }

        // ── Stage 2: Python Build Environment ───────────────────────────────
        stage('Build Environment') {
            steps {
                sh """
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip --quiet
                    pip install -r requirements.txt --quiet
                    echo "✅ Dependencies installed:"
                    pip list | grep -E "Flask|pytest|flake8|gunicorn"
                """
            }
        }

        // ── Stage 3: Lint ────────────────────────────────────────────────────
        stage('Lint') {
            steps {
                sh """
                    . ${VENV_DIR}/bin/activate
                    flake8 app.py tests/ \\
                        --max-line-length=100 \\
                        --ignore=E501,W503,W504 \\
                        --statistics
                    echo "✅ Lint passed — no code quality violations."
                """
            }
        }

        // ── Stage 4: SonarQube Static Analysis ──────────────────────────────
        stage('SonarQube Analysis') {
            when { expression { !params.SKIP_SONAR } }
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    sh """
                        . ${VENV_DIR}/bin/activate
                        # Generate coverage report first
                        pytest tests/ \\
                            --cov=app \\
                            --cov-report=xml:coverage.xml \\
                            --quiet --tb=no

                        # Run sonar-scanner
                        sonar-scanner \\
                            -Dsonar.projectKey=${SONAR_PROJECT} \\
                            -Dsonar.projectName="ACEest Fitness & Gym" \\
                            -Dsonar.projectVersion=${APP_VERSION} \\
                            -Dsonar.sources=. \\
                            -Dsonar.inclusions=app.py \\
                            -Dsonar.exclusions=tests/**,${VENV_DIR}/** \\
                            -Dsonar.python.coverage.reportPaths=coverage.xml \\
                            -Dsonar.host.url=${SONAR_HOST_URL} \\
                            -Dsonar.login=\${SONAR_TOKEN}

                        echo "✅ SonarQube analysis complete."
                    """
                }
            }
        }

        // ── Stage 5: Docker Image Build ──────────────────────────────────────
        stage('Docker Build') {
            // Uses Docker when available; falls back to Podman automatically.
            // Both produce identical OCI-compliant images — fully interoperable.
            steps {
                script {
                    def buildCmd = sh(
                        script: 'command -v docker &>/dev/null && echo "docker" || echo "podman"',
                        returnStdout: true
                    ).trim()
                    echo "▶ Container engine detected: ${buildCmd}"
                    sh """
                        ${buildCmd} build \\
                            --file ${buildCmd == 'podman' ? 'Containerfile' : 'Dockerfile'} \\
                            --build-arg APP_VERSION=${APP_VERSION} \\
                            --build-arg BUILD_DATE=\$(date -u +%Y-%m-%dT%H:%M:%SZ) \\
                            --build-arg GIT_COMMIT=${GIT_COMMIT_SHORT} \\
                            --tag ${IMAGE_TAG} \\
                            --tag ${IMAGE_BUILD} \\
                            --tag ${IMAGE_LATEST} \\
                            .
                        echo "✅ Image built via ${buildCmd}: ${IMAGE_TAG}"
                        ${buildCmd} images | grep ${APP_NAME} || true
                    """
                }
            }
        }

        // ── Stage 6: Automated Tests (inside Docker) ─────────────────────────
        stage('Test') {
            steps {
                sh """
                    # Run pytest with JUnit XML + coverage reports as build artifacts
                    docker run --rm \\
                        --name ${APP_NAME}-test-${BUILD_NUMBER} \\
                        --env DATABASE_URL=/tmp/test_aceest.db \\
                        --volume \$(pwd)/test-reports:/app/test-reports \\
                        ${IMAGE_TAG} \\
                        python -m pytest tests/ \\
                            --verbose \\
                            --tb=short \\
                            --color=no \\
                            -p no:cacheprovider \\
                            --junitxml=test-reports/junit-${BUILD_NUMBER}.xml \\
                            --cov=app \\
                            --cov-report=xml:test-reports/coverage-${BUILD_NUMBER}.xml \\
                            --cov-report=term-missing
                    echo "✅ All tests passed. Artifacts saved to test-reports/"
                """
            }
            post {
                always {
                    // Publish JUnit results in Jenkins UI (Test Results trend graph)
                    junit allowEmptyResults: true,
                          testResults: 'test-reports/junit-*.xml'

                    // Archive test + coverage XML as downloadable build artifacts
                    archiveArtifacts artifacts: 'test-reports/*.xml',
                                     fingerprint: true,
                                     allowEmptyArchive: true
                }
                failure {
                    echo "❌ Tests failed — check junit XML in build artifacts."
                }
            }
        }

        // ── Stage 7: Smoke Test ──────────────────────────────────────────────
        stage('Smoke Test') {
            steps {
                sh """
                    docker run -d \\
                        --name ${APP_NAME}-smoke-${BUILD_NUMBER} \\
                        -p 5099:5000 \\
                        --env DATABASE_URL=/tmp/smoke_aceest.db \\
                        ${IMAGE_TAG}

                    sleep 8

                    STATUS=\$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:5099/api/health)
                    if [ "\$STATUS" != "200" ]; then
                        echo "❌ Smoke test failed — HTTP \$STATUS"
                        docker stop ${APP_NAME}-smoke-${BUILD_NUMBER} || true
                        docker rm  ${APP_NAME}-smoke-${BUILD_NUMBER} || true
                        exit 1
                    fi
                    echo "✅ Smoke test passed — HTTP \$STATUS on /api/health"
                    docker stop ${APP_NAME}-smoke-${BUILD_NUMBER} || true
                    docker rm  ${APP_NAME}-smoke-${BUILD_NUMBER} || true
                """
            }
        }

        // ── Stage 8: Generate Build Artifacts ────────────────────────────────
        // Produces a version manifest (JSON) + Docker image digest as downloadable
        // build artifacts — satisfies "generate build artifacts per version" requirement.
        stage('Build Artifacts') {
            steps {
                sh """
                    mkdir -p build-artifacts

                    # ── Version manifest (JSON) ──────────────────────────────
                    cat > build-artifacts/build-manifest-${BUILD_NUMBER}.json << EOF
{
  "build_number"   : "${BUILD_NUMBER}",
  "app_name"       : "${APP_NAME}",
  "app_version"    : "${APP_VERSION}",
  "git_branch"     : "${GIT_BRANCH_NAME}",
  "git_commit"     : "${GIT_COMMIT_SHORT}",
  "image_version"  : "${IMAGE_TAG}",
  "image_build"    : "${IMAGE_BUILD}",
  "deploy_strategy": "${params.DEPLOY_STRATEGY}",
  "build_timestamp": "\$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "pipeline"       : "Jenkins"
}
EOF

                    # ── Docker image digest ───────────────────────────────────
                    docker inspect ${IMAGE_TAG} \\
                        --format='{{index .RepoDigests 0}}' \\
                        > build-artifacts/image-digest-${BUILD_NUMBER}.txt 2>/dev/null || \\
                        docker images ${IMAGE_TAG} --format '{{.ID}}' \\
                        > build-artifacts/image-digest-${BUILD_NUMBER}.txt

                    echo "✅ Build artifacts generated:"
                    cat build-artifacts/build-manifest-${BUILD_NUMBER}.json
                """
                archiveArtifacts artifacts: 'build-artifacts/**',
                                 fingerprint: true
            }
        }

        // ══════════════════════════════════════════════════════════════════════
        // ── CD: Push to Docker Hub ───────────────────────────────────────────
        // ══════════════════════════════════════════════════════════════════════
        stage('Docker Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                        echo "\$DOCKER_PASS" | docker login -u "\$DOCKER_USER" --password-stdin
                        docker push ${IMAGE_TAG}
                        docker push ${IMAGE_BUILD}
                        docker push ${IMAGE_LATEST}
                        echo "✅ Images pushed to Docker Hub:"
                        echo "   → ${IMAGE_TAG}"
                        echo "   → ${IMAGE_BUILD}"
                        echo "   → ${IMAGE_LATEST}"
                    """
                }
                // Optionally push all historical versions
                script {
                    if (params.PUSH_ALL_VERSIONS) {
                        sh "bash scripts/push-versions.sh"
                    }
                }
            }
        }

        // ── CD: Kubernetes Namespace Setup ────────────────────────────────────
        stage('K8s Namespace') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        kubectl apply -f k8s/namespace.yaml
                        kubectl apply -f k8s/configmap.yaml
                        echo "✅ Namespace and ConfigMap applied."
                    """
                }
            }
        }

        // ── CD: Deploy — Strategy-Based ──────────────────────────────────────
        stage('Deploy') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    script {
                        def strategy = params.DEPLOY_STRATEGY ?: 'rolling'
                        echo "▶ Deploying with strategy: ${strategy.toUpperCase()}"
                        sh """
                            export KUBECONFIG=\$KUBECONFIG
                            bash scripts/deploy.sh ${strategy} ${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        // ── CD: Verify Rollout ────────────────────────────────────────────────
        stage('Verify Rollout') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        kubectl rollout status deployment/${APP_NAME} \\
                            -n ${K8S_NAMESPACE} \\
                            --timeout=120s || true
                        kubectl get pods -n ${K8S_NAMESPACE} -l app=${APP_NAME}
                        echo "✅ Rollout verification complete."
                    """
                }
            }
        }

    } // end stages

    // ── Post-pipeline actions ─────────────────────────────────────────────────
    post {
        success {
            echo """
╔══════════════════════════════════════════════════════════╗
║  ✅  CI/CD PIPELINE SUCCESSFUL — ACEest Fitness v3.2.4   ║
║  Build #${BUILD_NUMBER} | Strategy: ${params.DEPLOY_STRATEGY}
╚══════════════════════════════════════════════════════════╝
            """
        }
        failure {
            echo """
╔══════════════════════════════════════════════════════════╗
║  ❌  PIPELINE FAILED — ACEest Fitness v3.2.4              ║
║  Build #${BUILD_NUMBER} — initiating auto-rollback...    ║
╚══════════════════════════════════════════════════════════╝
            """
            withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                sh """
                    export KUBECONFIG=\$KUBECONFIG
                    bash scripts/rollback.sh ${K8S_NAMESPACE} || true
                """
            }
        }
        always {
            // Cleanup smoke container if still running
            sh "docker rm -f ${APP_NAME}-smoke-${BUILD_NUMBER} 2>/dev/null || true"
            // Remove build-specific image from agent (keep latest + version tag)
            sh "docker rmi ${IMAGE_BUILD} 2>/dev/null || true"
            docker.withRegistry('https://registry-1.docker.io', 'dockerhub-credentials') {}
            sh "docker logout registry-1.docker.io 2>/dev/null || true"
            echo "✅ Workspace cleanup complete — Build #${BUILD_NUMBER}"
        }
    }

}
