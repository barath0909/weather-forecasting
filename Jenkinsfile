pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials-id')
        GITHUB_CREDENTIALS    = credentials('github-credentials-id')
        IMAGE_NAME            = 'barathj09/weather-forecasting-app'
        IMAGE_TAG             = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Set Up & Run Unit Tests') {
            steps {
                bat '''
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    python -m pytest
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                bat "docker build -t %IMAGE_NAME%:%IMAGE_TAG% -t %IMAGE_NAME%:latest ."
            }
        }

        stage('Push Image to Docker Hub') {
            steps {
                bat '''
                    docker login -u %DOCKERHUB_CREDENTIALS_USR% -p %DOCKERHUB_CREDENTIALS_PSW%
                    docker push %IMAGE_NAME%:%IMAGE_TAG%
                    docker push %IMAGE_NAME%:latest
                '''
            }
        }

        stage('Update GitOps Manifest') {
            steps {
                bat '''
                    powershell -Command "(Get-Content k8s/deployment.yaml) -replace 'image: barathj09/weather-forecasting-app:.*', ('image: barathj09/weather-forecasting-app:' + $env:IMAGE_TAG) | Set-Content k8s/deployment.yaml"
                    git config user.name "Jenkins CI"
                    git config user.email "jenkins@barath.dev"
                    git add k8s/deployment.yaml
                    git commit -m "chore(k8s): update image tag to %IMAGE_TAG% [skip ci]" || echo No changes to commit
                    git push https://%GITHUB_CREDENTIALS_USR%:%GITHUB_CREDENTIALS_PSW%@github.com/barath0909/weather-forecasting.git HEAD:refs/heads/main
                '''
            }
        }
    }

    post {
        always {
            bat 'docker logout || rem'
            cleanWs()
        }
    }
}