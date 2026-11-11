pipeline{
    agent any

    environment {
        APP_VERSION = '1.0.0'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    stages {
        stage('Checkout')
            steps {
                checkout scm
                sh 'git log -1 --oneline'
                script {
                    env.SHORT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }

        stage('Test') {
            steps {
                sh '''
                        python3 -m venv .ci-venv
                        . .ci-venv/bin/activate
                        pip install -q -r chat-api/requirements.txt
                        cd chat-api
                        timeout 60 python -c "import app; print('chat-api imports OK')"
                '''
            }
        }

        stage('Test')
            steps {
                sh '''
                    docker build \
                      --build-arg APP_VERSION=${APP_VERSION} \
                      --build-arg GIT_COMMIT=${SHORT_COMMIT} \
                      -t chat-api:${SHORT_COMMIT} chat-api

                    docker build \
                      --build-arg APP_VERSION=${APP_VERSION} \
                      --build-arg GIT_COMMIT=${SHORT_COMMIT} \
                      -t chat-frontend:${SHORT_COMMIT} website

                '''

            }
        }
    }

    post {
        always {
            deleteDir()   // clean the workspace after each build
        }
    }
}