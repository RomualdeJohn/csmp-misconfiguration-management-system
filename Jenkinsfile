#!/bin/groovy

@Library('cpd-workflowlibs@master') _

// --- Configuration for all services ---
def services = [
    'backend': [
        appName: 'cspm-misconfig-mgmt-system-be',
        contextPath: '.',
        kustomizePath: 'k8s'
    ]
]

pipeline {
    agent {
        kubernetes {
            inheritFrom "jenkins-buildah-agent"
        }
    }

    options {
        timestamps()
        ansiColor('xterm')
    }

    parameters {
        string(name: 'IMAGE_TAG', defaultValue: '', description: 'Optional image tag (defaults to BUILD_TIMESTAMP)')
        choice(name: 'SERVICE', choices: ['all'] + services.keySet().toList(), description: 'Select the service to build and deploy.')
    }

    environment {
        PROJECT_NAME = "oss-operation-cspm-system"
        REGISTRY_URL = "registry-jpw2.r-local.net"
        K8S_CLUSTER_ID = "jpw2-caas1-dev3"
        // Cluster namespace (where manifests are applied). cpd.kubectl loads Jenkins secret text
        // ${K8S_CLUSTER_ID}_${K8S_NAMESPACE}_k8s-token — must match credential id, not the Jenkins folder name.
        K8S_NAMESPACE = "oss-operation-cspm-system"
    }

    stages {
        stage('Debug Environment') {
            steps {
                sh 'printenv | sort'
            }
        }

        stage('Build and Deploy Services') {
            steps {
                script {
                    def servicesToProcess = (params.SERVICE == 'all') ? services.keySet() : [params.SERVICE]
                    def parallelStages = [:]

                    for (serviceName in servicesToProcess) {
                        def config = services[serviceName]
                        def appName = config.appName
                        def contextPath = config.contextPath
                        def kustomizePath = config.kustomizePath
                        def fullImageName = "${REGISTRY_URL}/${PROJECT_NAME}/${appName}"
                        def imageTag = "${params.IMAGE_TAG ?: BUILD_TIMESTAMP}"
                        def manifestFile = "resource-${appName}.yaml"

                        parallelStages["Process ${serviceName.capitalize()}"] = {
                            stage("Processing ${serviceName.capitalize()}") {

                                stage("Build Image: ${appName}") {
                                    container('buildah') {
                                        echo "Logging in into registry..."
                                        withCredentials([usernamePassword(credentialsId: "jpw2-oss-operation-cspm-misconfig-mgmt-system-registry-bot", usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                                            sh "buildah login --username \$USERNAME --password \$PASSWORD ${REGISTRY_URL}"
                                        }

                                        echo "Building image for ${appName}..."
                                        sh """
                                            buildah bud \
                                            -f "${contextPath}/Dockerfile" \
                                            -t "${fullImageName}:latest" \
                                            "${contextPath}"
                                        """

                                        echo "Tagging image with ${imageTag}..."
                                        sh "buildah tag ${fullImageName}:latest ${fullImageName}:${imageTag}"

                                        echo "Pushing images for ${appName}..."
                                        sh "buildah push ${fullImageName}:latest"
                                        sh "buildah push ${fullImageName}:${imageTag}"
                                    }
                                }

                                stage("Build Manifest: ${appName}") {
                                    dir(kustomizePath) {
                                        sh label: "Generate ${manifestFile} with kustomize", script: """
                                            kubectl kustomize . > ${WORKSPACE}/${manifestFile}
                                        """
                                    }
                                    archiveArtifacts artifacts: manifestFile, fingerprint: true
                                }

                                stage("Apply Manifest: ${appName}") {
                                    echo "Applying manifest: ${manifestFile} to namespace ${K8S_NAMESPACE}"
                                    cpd.kubectl("apply -f ${WORKSPACE}/${manifestFile}")
                                }
                            }
                        }
                    }
                    parallel parallelStages
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded!'
        }
        unstable {
            echo 'Pipeline is unstable.'
        }
        failure {
            echo 'Pipeline failed.'
        }
        changed {
            echo 'Pipeline result changed.'
        }
        always {
            script {
                sh 'rm -f resource-*.yaml'
                currentBuild.result = currentBuild.currentResult
            }
        }
    }
}

