#!/bin/bash

# ML Pharma Application Deployment Script
# This script builds and deploys the application to Azure Kubernetes Service

set -e  # Exit on any error

# Configuration
ACR_NAME="pharmlacr"
RESOURCE_GROUP="pharma-ml-rg"
AKS_CLUSTER="pharma-aks"
NAMESPACE="pharma-ml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists az; then
        print_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command_exists kubectl; then
        print_error "kubectl is not installed. Please install it first."
        exit 1
    fi
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Login to Azure and ACR
azure_login() {
    print_status "Checking Azure login status..."
    
    if ! az account show >/dev/null 2>&1; then
        print_status "Logging into Azure..."
        az login
    fi
    
    print_status "Logging into Azure Container Registry..."
    az acr login --name $ACR_NAME
    
    print_success "Azure login completed"
}

# Build and push Docker images
build_and_push_images() {
    print_status "Building Docker images..."
    
    # Build FastAPI image
    print_status "Building FastAPI image..."
    docker build -f docker/Dockerfile.fastapi -t ${ACR_NAME}.azurecr.io/pharma-fastapi:latest .
    
    # Build Streamlit image
    print_status "Building Streamlit image..."
    docker build -f docker/Dockerfile.streamlit -t ${ACR_NAME}.azurecr.io/pharma-streamlit:latest .
    
    print_status "Pushing images to Azure Container Registry..."
    
    # Push FastAPI image
    docker push ${ACR_NAME}.azurecr.io/pharma-fastapi:latest
    
    # Push Streamlit image
    docker push ${ACR_NAME}.azurecr.io/pharma-streamlit:latest
    
    print_success "Images built and pushed successfully"
}

# Update Cosmos DB secrets
update_secrets() {
    print_status "Updating Kubernetes secrets..."
    
    # Get Cosmos DB connection details
    COSMOS_ENDPOINT=$(az cosmosdb show --name pharma-cosmos --resource-group $RESOURCE_GROUP --query documentEndpoint -o tsv)
    COSMOS_KEY=$(az cosmosdb keys list --name pharma-cosmos --resource-group $RESOURCE_GROUP --query primaryMasterKey -o tsv)
    
    if [ -z "$COSMOS_ENDPOINT" ] || [ -z "$COSMOS_KEY" ]; then
        print_error "Failed to retrieve Cosmos DB credentials"
        exit 1
    fi
    
    # Encode credentials
    COSMOS_ENDPOINT_B64=$(echo -n "$COSMOS_ENDPOINT" | base64 -w 0)
    COSMOS_KEY_B64=$(echo -n "$COSMOS_KEY" | base64 -w 0)
    
    # Update secret file
    sed -i "s|cosmos-endpoint:.*|cosmos-endpoint: $COSMOS_ENDPOINT_B64|" k8s/secret.yaml
    sed -i "s|cosmos-key:.*|cosmos-key: $COSMOS_KEY_B64|" k8s/secret.yaml
    
    print_success "Secrets updated"
}

# Get AKS credentials
get_aks_credentials() {
    print_status "Getting AKS credentials..."
    az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER --overwrite-existing
    print_success "AKS credentials configured"
}

# Deploy to Kubernetes
deploy_to_k8s() {
    print_status "Deploying to Kubernetes..."
    
    # Apply manifests in order
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/secret.yaml
    kubectl apply -f k8s/fastapi-deployment.yaml
    kubectl apply -f k8s/streamlit-deployment.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/ingress.yaml
    kubectl apply -f k8s/hpa.yaml
    
    print_success "Kubernetes manifests applied"
}

# Wait for deployments to be ready
wait_for_deployments() {
    print_status "Waiting for deployments to be ready..."
    
    kubectl wait --for=condition=available --timeout=300s deployment/fastapi-deployment -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/streamlit-deployment -n $NAMESPACE
    
    print_success "All deployments are ready"
}

# Get application URLs
get_application_urls() {
    print_status "Getting application URLs..."
    
    # Wait for ingress to get an IP
    sleep 30
    
    INGRESS_IP=$(kubectl get ingress pharma-ingress -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ -z "$INGRESS_IP" ]; then
        print_warning "Ingress IP not yet assigned. You can check later with:"
        echo "kubectl get ingress pharma-ingress -n $NAMESPACE"
    else
        print_success "Application deployed successfully!"
        echo ""
        echo "Application URLs:"
        echo "  Streamlit UI: http://$INGRESS_IP"
        echo "  FastAPI Docs: http://$INGRESS_IP/api/docs"
        echo "  API Health: http://$INGRESS_IP/api/health"
    fi
}

# Check deployment status
check_deployment_status() {
    print_status "Checking deployment status..."
    
    echo ""
    echo "Pods:"
    kubectl get pods -n $NAMESPACE
    
    echo ""
    echo "Services:"
    kubectl get services -n $NAMESPACE
    
    echo ""
    echo "Ingress:"
    kubectl get ingress -n $NAMESPACE
}

# Main deployment function
main() {
    echo "============================================"
    echo "ML Pharma Application Deployment"
    echo "============================================"
    echo ""
    
    check_prerequisites
    azure_login
    build_and_push_images
    update_secrets
    get_aks_credentials
    deploy_to_k8s
    wait_for_deployments
    get_application_urls
    check_deployment_status
    
    print_success "Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Wait a few minutes for all services to be fully ready"
    echo "2. Access the Streamlit UI to test the application"
    echo "3. Check the metrics dashboard for system performance"
    echo "4. Run stress tests with: locust -f locustfile.py --host=http://YOUR_IP"
}

# Run main function
main "$@"
