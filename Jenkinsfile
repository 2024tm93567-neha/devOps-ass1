// ─────────────────────────────────────────────────────────────────────────────
// ACEest Fitness & Gym — Jenkins Declarative Pipeline
// ─────────────────────────────────────────────────────────────────────────────

pipeline {

    agent any

    environment {
        APP_NAME     = "aceest-fitness"
        IMAGE_TAG    = "${APP_NAME}:${BUILD_NUMBER}"
        IMAGE_LATEST = "${APP_NAME}:latest"
        VENV_DIR     = ".venv"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
    }

    stages {

        stage('Checkout') {
            steps {
                echo "╔══════════════════════════════════════════╗"
                echo "║  ACEest Fitness — Jenkins BUILD Pipeline ║"
                echo "╚══════════════════════════════════════════╝"
                echo "▶ Checking out source from GitHub..."
                checkout scm
                echo "✅ Checkout complete — Build #${BUILD_NUMBER}"
            }
        }

        stage('Build Environment') {
            steps {
                echo "▶ Creating Python virtual environment and installing dependencies..."
                sh """
                    python3 -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip --quiet
                    pip install -r requirements.txt --quiet
                    echo "✅ Dependencies installed:"
                    pip list | grep -E "Flask|pytest|flake8"
                """
            }
        }

        stage('Lint') {
            steps {
                echo "▶ Running flake8 static analysis..."
                sh """
                    . ${VENV_DIR}/bin/activate
                    flake8 app.py tests/ \\
                        --max-line-length=100 \\
                        --ignore=E501,W503,W504 \\
                        --statistics
                    echo "✅ Lint passed — code quality gate cleared."
                """
            }
        }

        stage('Docker Build') {
            steps {
                echo "▶ Building Docker image: ${IMAGE_TAG}..."
                sh """
                    docker build \\
                        --tag ${IMAGE_TAG} \\
                        --tag ${IMAGE_LATEST} \\
                        .
                    echo "✅ Docker image built successfully."
                    docker images ${APP_NAME}
                """
            }
        }

        stage('Test') {
            steps {
                echo "▶ Running pytest suite inside Docker container..."
                sh """
                    docker run --rm \\
                        --name ${APP_NAME}-test-${BUILD_NUMBER} \\
                        ${IMAGE_TAG} \\
                        python -m pytest tests/ \\
                            --verbose \\
                            --tb=short \\
                            --color=no \\
                            -p no:cacheprovider
                    echo "✅ All tests passed — quality gate cleared."
                """
            }
            post {
                always { echo "Test stage finished for build #${BUILD_NUMBER}" }
                failure { echo "❌ Test stage failed — investigate pytest output above." }
            }
        }

        stage('Smoke Test') {
            steps {
                echo "▶ Starting container for smoke test..."
                sh """
                    docker run -d \\
                        --name ${APP_NAME}-smoke-${BUILD_NUMBER} \\
                        -p 5099:5000 \\
                        ${IMAGE_TAG}

                    sleep 5

                    STATUS=\$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5099/api/health)
                    if [ "\$STATUS" != "200" ]; then
                        echo "❌ Health probe returned HTTP \$STATUS"
                        docker stop ${APP_NAME}-smoke-${BUILD_NUMBER} || true
                        docker rm  ${APP_NAME}-smoke-${BUILD_NUMBER} || true
                        exit 1
                    fi
                    echo "✅ Smoke test passed — HTTP 200 on /api/health"

                    docker stop ${APP_NAME}-smoke-${BUILD_NUMBER} || true
                    docker rm  ${APP_NAME}-smoke-${BUILD_NUMBER} || true
                """
            }
        }

    }

    post {
        success {
            echo """
╔══════════════════════════════════════════════════╗
║  ✅  BUILD SUCCESSFUL  — ACEest Fitness v3.2.4   ║
║  Build #${BUILD_NUMBER} passed all quality gates  ║
╚══════════════════════════════════════════════════╝
            """
        }
        failure {
            echo """
╔══════════════════════════════════════════════════╗
║  ❌  BUILD FAILED  — ACEest Fitness v3.2.4        ║
║  Build #${BUILD_NUMBER} — check console output    ║
╚══════════════════════════════════════════════════╝
            """
            sh "docker rm -f ${APP_NAME}-smoke-${BUILD_NUMBER} 2>/dev/null || true"
        }
        always {
            sh "docker rmi ${IMAGE_TAG} 2>/dev/null || true"
            echo "Workspace cleanup complete."
        }
    }

}
