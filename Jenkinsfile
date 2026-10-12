pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-credentials-id')
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
                script {
                    bat "docker build -t %IMAGE_NAME%:%IMAGE_TAG% -t %IMAGE_NAME%:latest ."
                }
            }
        }

        stage('Push Image to Docker Hub') {
            steps {
                script {
                    bat '''
                        docker login -u %DOCKERHUB_CREDENTIALS_USR% -p %DOCKERHUB_CREDENTIALS_PSW%
                        docker push %IMAGE_NAME%:%IMAGE_TAG%
                        docker push %IMAGE_NAME%:latest
                    '''
                }
            }
        }
    }

    post {
        always {
            bat 'docker logout || rem'
            cleanWs()
        }
        success {
            echo "CI pipeline completed successfully. Image pushed to Docker Hub!"
        }
        failure {
            echo "Pipeline failed! Please inspect logs."
        }
    }
}