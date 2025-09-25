@echo off
set -e

echo 🐳 Building Todo API...
docker build -t todo-api:v1.0 .

where minikube >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('minikube docker-env') do %%i
    docker build -t todo-api:v1.0 .
)

echo ☸️ Deploying to Kubernetes...
kubectl apply -f k8s/

echo ⏳ Waiting for deployments...
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n todo-app
kubectl wait --for=condition=available --timeout=300s deployment/todo-api -n todo-app

echo ✅ Todo API deployed!
echo 🧪 Test the API:
echo    kubectl port-forward -n todo-app service/todo-api-service 8080:80
echo    curl http://localhost:8080/api/todos
