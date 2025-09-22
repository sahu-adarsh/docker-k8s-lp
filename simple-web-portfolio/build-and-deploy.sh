#!/bin/bash
set -e

echo "🐳 Building Docker image..."
docker build -t portfolio:v1.0 .

# For minikube
if command -v minikube &> /dev/null; then
    eval $(minikube docker-env)
    docker build -t portfolio:v1.0 .
fi

echo "☸️ Deploying to Kubernetes..."
kubectl apply -f k8s/

echo "⏳ Waiting for deployment..."
kubectl wait --for=condition=available --timeout=300s deployment/portfolio-app -n portfolio

echo "✅ Deployment complete!"
echo "🌐 Access your app:"
echo "   kubectl port-forward -n portfolio service/portfolio-service 8080:80"
echo "   Then visit: http://localhost:8080"