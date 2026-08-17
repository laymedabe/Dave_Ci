pipeline {
    agent any
    environment {
        REGISTRY = '192.168.10.23:5000'
        IMAGE_NAME = "${REGISTRY}/portal-d"
        MANIFEST_REPO = 'git@github.com:laymedabe/Dave_Cd.git'
    }
    stages {
        stage('Determine Target Environment') {
            steps {
                script {
                    if (env.TAG_NAME) {
                        env.IMAGE_TAG = env.TAG_NAME
                        env.TARGET_ENV = 'production'
                    } else if (env.BRANCH_NAME == 'main') {
                        env.IMAGE_TAG = "build-${env.BUILD_NUMBER}"
                        env.TARGET_ENV = 'staging'
                    } else {
                        error("Skipping deployment: Not on main branch or a git tag.")
                    }
                }
            }
        }
        stage('Build & Push Docker Image') {
            steps {
                script {
                    docker.withRegistry("http://${REGISTRY}", 'jenkins-registry-creds') {
                        def customImage = docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                        customImage.push()
                    }
                }
            }
        }
        stage('Update Manifests') {
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: 'jenkins-git-creds', keyFileVariable: 'SSH_KEY')]) {
                    sh """
                    export GIT_SSH_COMMAND="ssh -i $SSH_KEY -o StrictHostKeyChecking=no"
                    git clone ${MANIFEST_REPO} manifest-repo
                    cd manifest-repo
                    
                    sed -i "s|image: ${IMAGE_NAME}:.*|image: ${IMAGE_NAME}:${IMAGE_TAG}|g" manifests/${TARGET_ENV}/deployment.yaml
                    
                    git config user.name "Jenkins CI"
                    git config user.email "jenkins@ci.local"
                    git add manifests/${TARGET_ENV}/deployment.yaml
                    git commit -m "Deploy ${TARGET_ENV} to ${IMAGE_TAG}" || echo "No changes"
                    git push origin main
                    """
                }
            }
        }
    }
}
