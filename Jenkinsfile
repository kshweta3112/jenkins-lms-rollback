
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    parameters {
        choice(
            name: 'SIMULATE_FAILURE',
            choices: ['false', 'true'],
            description: 'Set true to test rollback'
        )
    }

    environment {
        APP_NAME = 'lms-app'
        APP_PORT = '8081'
    }

    stages {
        stage('Prepare') {
            steps {
                sh '''
                    rm -f previous-image-tag.txt
                    test -f Dockerfile
                    test -f app.py
                    test -f requirements.txt
                    docker info >/dev/null
                '''
            }
        }

        stage('Build Image') {
            steps {
                sh '''
                    set -eu
                    docker build -t lms-app:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Save Previous Version') {
            steps {
                sh '''
                    set -eu
                    docker inspect "$APP_NAME" >/dev/null

                    CURRENT_IMAGE=$(docker inspect \
                      --format='{{.Image}}' "$APP_NAME")

                    ROLLBACK_TAG="lms-app:rollback-${BUILD_NUMBER}"

                    docker tag "$CURRENT_IMAGE" "$ROLLBACK_TAG"
                    echo "$ROLLBACK_TAG" > previous-image-tag.txt

                    docker image inspect "$ROLLBACK_TAG" >/dev/null
                    echo "Previous image saved as $ROLLBACK_TAG"
                '''
            }
        }

        stage('Deploy New Version') {
            steps {
                sh '''
                    set -eu
                    docker rm -f "$APP_NAME"

                    docker run -d \
                      --name "$APP_NAME" \
                      --restart unless-stopped \
                      -p ${APP_PORT}:8080 \
                      -e APP_VERSION=v${BUILD_NUMBER} \
                      -e HEALTH_FAIL=${SIMULATE_FAILURE} \
                      lms-app:${BUILD_NUMBER}
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    set -eu
                    healthy=false

                    for i in $(seq 1 12); do
                        if curl -fsS \
                          http://127.0.0.1:${APP_PORT}/health \
                          -o /tmp/lms-health.json &&
                          grep -q '"status":"UP"' /tmp/lms-health.json; then
                            healthy=true
                            break
                        fi

                        echo "Health check attempt $i failed"
                        sleep 5
                    done

                    if [ "$healthy" != true ]; then
                        echo "New version failed health check"
                        exit 1
                    fi

                    cat /tmp/lms-health.json
                '''
            }
        }
    }

    post {
        failure {
            script {
                if (fileExists('previous-image-tag.txt')) {
                    int result = sh(
                        returnStatus: true,
                        script: '''
                            set -eu
                            ROLLBACK_TAG=$(cat previous-image-tag.txt)
                            docker image inspect "$ROLLBACK_TAG" >/dev/null

                            docker rm -f "$APP_NAME" || true

                            docker run -d \
                              --name "$APP_NAME" \
                              --restart unless-stopped \
                              -p ${APP_PORT}:8080 \
                              -e APP_VERSION=rollback \
                              "$ROLLBACK_TAG"

                            healthy=false
                            for i in $(seq 1 12); do
                                if curl -fsS \
                                  http://127.0.0.1:${APP_PORT}/health \
                                  -o /tmp/lms-rollback-health.json &&
                                  grep -q '"status":"UP"' /tmp/lms-rollback-health.json; then
                                    healthy=true
                                    break
                                fi
                                sleep 5
                            done

                            if [ "$healthy" != true ]; then
                                docker logs "$APP_NAME" || true
                                exit 1
                            fi

                            echo "Rollback completed successfully"
                            cat /tmp/lms-rollback-health.json
                        '''
                    )

                    if (result != 0) {
                        error('CRITICAL: Rollback failed; manual intervention required')
                    }
                } else {
                    echo 'No previous image was saved; deployment was not rolled back.'
                }
            }
        }

        success {
            echo 'Deployment successful. LMS is healthy.'
        }

        always {
            echo 'Pipeline finished.'
        }
    }
}
