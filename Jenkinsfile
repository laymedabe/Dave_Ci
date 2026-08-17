pipeline {
    // Run this pipeline on any available Jenkins worker node
    agent any
    
    // Global environment variables used throughout the pipeline
    environment {
        // Define the private Docker registry IP and Port
        REGISTRY = '192.168.10.23:5000'
        // Define the full image name
        IMAGE_NAME = "${REGISTRY}/portal-d"
        // Target repository for our Kubernetes manifests
        MANIFEST_REPO = 'git@github.com:laymedabe/Dave_Cd.git'
    }
    
    stages {
        stage('Determine Target Environment') {
            steps {
                script {
                    // If Jenkins was triggered by a Git Tag (e.g. v1.0.0)
                    if (env.TAG_NAME) {
                        env.IMAGE_TAG = env.TAG_NAME
                        env.TARGET_ENV = 'production'
                    } 
                    // If Jenkins was triggered by a commit to the 'main' branch
                    else if (env.BRANCH_NAME == 'main') {
                        env.IMAGE_TAG = "build-${env.BUILD_NUMBER}"
                        env.TARGET_ENV = 'staging'
                    } 
                    // Abort the build if it's an unrecognized branch
                    else {
                        error("Skipping deployment: Not on main branch or a git tag.")
                    }
                }
            }
        }
        
        stage('Build & Push Docker Image') {
            steps {
                script {
                    // Authenticate with the private Docker registry using Jenkins credentials
                    docker.withRegistry("http://${REGISTRY}", 'jenkins-registry-creds') {
                        // Build the Dockerfile using the tag we determined in the first stage
                        def customImage = docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                        // Push the new image to the remote registry
                        customImage.push()
                    }
                }
            }
        }
        
        stage('Update Manifests') {
            steps {
                // Authenticate to GitHub using an SSH Private Key stored in Jenkins
                withCredentials([sshUserPrivateKey(credentialsId: 'jenkins-git-creds', keyFileVariable: 'SSH_KEY')]) {
                    sh """
                    # Disable strict host checking to prevent SSH prompts blocking the pipeline
                    export GIT_SSH_COMMAND="ssh -i $SSH_KEY -o StrictHostKeyChecking=no"
                    
                    # Clone the manifest repository
                    git clone ${MANIFEST_REPO} manifest-repo
                    cd manifest-repo
                    
                    # Use 'sed' to search deployment.yaml and replace the old image tag with the newly built one
                    sed -i "s|image: ${IMAGE_NAME}:.*|image: ${IMAGE_NAME}:${IMAGE_TAG}|g" manifests/${TARGET_ENV}/deployment.yaml
                    
                    # Configure git identity for the automated commit
                    git config user.name "Jenkins CI"
                    git config user.email "jenkins@ci.local"
                    
                    # Stage, commit, and push the updated deployment.yaml to GitHub
                    git add manifests/${TARGET_ENV}/deployment.yaml
                    git commit -m "Deploy ${TARGET_ENV} to ${IMAGE_TAG}" || echo "No changes"
                    git push origin main
                    """
                }
            }
        }
    }
}
