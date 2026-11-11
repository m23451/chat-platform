pipeline {
    agent any

    environment {
        APP_VERSION = '1.0.0'
        REGISTRY    = '026146807811.dkr.ecr.eu-north-1.amazonaws.com'
        AWS_REGION  = 'eu-north-1'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --oneline'
                script {
                    env.SHORT_COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Test') {
            steps {
                sh '''
                    python3 -m venv .ci-venv
                    . .ci-venv/bin/activate
                    pip install -q -r chat-api/requirements.txt pytest
                    cd chat-api
                    timeout 60 python -c "import app; print('chat-api imports OK')"
                    pytest tests -v
                '''
            }
        }

        stage('Build images') {
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

        stage('Push to ECR') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'aws-ecr-push',
                                                  usernameVariable: 'AWS_ACCESS_KEY_ID',
                                                  passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
                    sh '''
                        docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY amazon/aws-cli \
                            ecr get-login-password --region $AWS_REGION \
                          | docker login --username AWS --password-stdin $REGISTRY

                        for app in chat-api chat-frontend; do
                            docker tag  $app:$SHORT_COMMIT $REGISTRY/chat-site/$app:$SHORT_COMMIT
                            docker push $REGISTRY/chat-site/$app:$SHORT_COMMIT
                        done

                        docker logout $REGISTRY
                    '''
                }   // closes withCredentials
            }       // closes steps
        }           // closes stage('Push to ECR')  ← this was missing
    }               // closes stages

    post {
        always {
            deleteDir()   // clean the workspace after each build
        }
    }
}