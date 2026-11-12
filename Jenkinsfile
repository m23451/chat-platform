pipeline {
    agent any

    environment {
        APP_VERSION = '1.0.0'
        REGISTRY    = '026146807811.dkr.ecr.eu-north-1.amazonaws.com'
        AWS_REGION  = 'eu-north-1'
        REPO        = 'github.com/m23451/chat-platform.git'
        STAGING_URL = 'http://a4336909f9e2f41069a3e45be725e5ff-1880544154.eu-north-1.elb.amazonaws.com:8080'
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
                    env.SKIP_CI = sh(script: 'git log -1 --pretty=%B | grep -q "\\[skip ci\\]" && echo true || echo false', returnStdout: true).trim()
                }
            }
        }

        stage('Test') {
            when { expression { env.SKIP_CI != 'true' } }
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
            when { expression { env.SKIP_CI != 'true' } }
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
            when { expression { env.SKIP_CI != 'true' } }
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
                }
            }
        }

        stage('Deploy to staging') {
            when {
                allOf {
                    anyOf { branch 'develop'; branch 'main' }
                    expression { env.SKIP_CI != 'true' }
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-token',
                                                  usernameVariable: 'GIT_USER',
                                                  passwordVariable: 'GIT_TOKEN')]) {
                    sh '''
                        rm -rf deploy && git clone -q --depth 1 -b develop https://$REPO deploy
                        cd deploy
                        sed -i "s/newTag: .*/newTag: $SHORT_COMMIT/" k8s/overlays/staging/kustomization.yaml
                        git config user.name  "Jenkins"
                        git config user.email "jenkins@chat-platform.local"
                        # Only commit if the tag actually changed
                        git diff --quiet || {
                            git commit -qam "Deploy $SHORT_COMMIT to staging [skip ci]"
                            git push -q https://$GIT_USER:$GIT_TOKEN@$REPO HEAD:develop
                        }
                    '''
                }
            }
        }

        stage('Smoke test staging') {
            when {
                allOf {
                    anyOf { branch 'develop'; branch 'main' }
                    expression { env.SKIP_CI != 'true' }
                }
            }
            steps {
                sh '''
                    # 1. Wait for Argo CD to roll out the new version
                    # TODO: replace with the /api/info version check once that endpoint is reachable
                    echo "Waiting 4 minutes for Argo CD to deploy..."
                    sleep 240

                    # 2. Check the key features work
                    curl -fs $STAGING_URL/healthz                                   # website up
                    curl -fs "$STAGING_URL/api/messages?limit=1" > /dev/null        # history loads (DB ok)
                    curl -fs -X POST -H "Content-Type: application/json" \
                         -d "{\\"author\\":\\"smoke-test\\",\\"text\\":\\"smoke test $SHORT_COMMIT\\"}" \
                         $STAGING_URL/api/messages > /dev/null                      # sending works
                    echo "Smoke tests passed"
                '''
            }
        }

        stage('Approve prod') {
            when {
                allOf {
                    branch 'main'
                    expression { env.SKIP_CI != 'true' }
                }
            }
            steps {
                timeout(time: 1, unit: 'HOURS') {
                    input message: "Staging passed. Deploy ${env.SHORT_COMMIT} to prod?", ok: 'Deploy'
                }
            }
        }

        stage('Deploy to prod') {
            when {
                allOf {
                    branch 'main'
                    expression { env.SKIP_CI != 'true' }
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-token',
                                                  usernameVariable: 'GIT_USER',
                                                  passwordVariable: 'GIT_TOKEN')]) {
                    sh '''
                        # Fresh copy of main (the branch Argo CD watches for prod)
                        rm -rf deploy && git clone -q --depth 1 -b main https://$REPO deploy
                        cd deploy
                        sed -i "s/newTag: .*/newTag: $SHORT_COMMIT/" k8s/overlays/prod/kustomization.yaml
                        git config user.name  "Jenkins"
                        git config user.email "jenkins@chat-platform.local"
                        git diff --quiet || {
                            git commit -qam "Deploy $SHORT_COMMIT to prod [skip ci]"
                            git push -q https://$GIT_USER:$GIT_TOKEN@$REPO HEAD:main
                        }
                    '''
                }
            }
        }
    }

    post {
        always {
            deleteDir()
        }
    }
}