# ML Pharma Application

A complete machine learning application for pharmaceutical treatment effectiveness prediction, built with Streamlit, FastAPI, and deployed on Azure Kubernetes Service.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   FastAPI API   │    │   Azure         │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│   Cosmos DB     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Container     │    │   Container     │    │   Azure         │
│   Metrics       │    │   Metrics       │    │   Load Balancer │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## ✨ Features

- **🔬 ML Predictions**: Logistic regression model for treatment effectiveness
- **📊 Real-time Metrics**: Container and application performance monitoring
- **🎯 Interactive UI**: User-friendly Streamlit interface
- **🚀 Scalable API**: FastAPI backend with automatic scaling
- **☁️ Cloud Native**: Kubernetes deployment on Azure
- **💾 Data Storage**: Azure Cosmos DB integration
- **📈 Load Testing**: Locust-based stress testing

## 🛠️ Prerequisites

### Software Requirements
- Python 3.12.10
- Docker Desktop
- Azure CLI
- kubectl
- Git

### Azure Resources
- Azure Container Registry (ACR)
- Azure Kubernetes Service (AKS)
- Azure Cosmos DB
- Resource Group

## 🚀 Quick Start

### 1. Local Development

```bash
# Clone the repository
git clone <your-repo-url>
cd ml-pharma

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend
python app/main.py

# In another terminal, start Streamlit frontend
streamlit run streamlit_app/main.py
```

### 2. Docker Development

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access the application
# Streamlit UI: http://localhost:8501
# FastAPI Docs: http://localhost:8000/docs
```

### 3. Azure Deployment

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

## 🔧 Configuration

### Environment Variables

#### FastAPI Backend
```bash
COSMOS_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key
PYTHONPATH=/app
```

#### Streamlit Frontend
```bash
API_URL=http://fastapi-service:8000
PYTHONPATH=/app
```

### Kubernetes Secrets

Update the Cosmos DB credentials in `k8s/secret.yaml`:

```bash
# Encode your credentials
echo -n "your-cosmos-endpoint" | base64
echo -n "your-cosmos-key" | base64

# Update the secret.yaml file with encoded values
```

## 🏥 ML Model

### Features
The model uses 8 input features:
- **Drug Concentration** (mg/mL): Active ingredient concentration
- **Patient Age** (years): Patient age
- **Patient Weight** (kg): Patient body weight
- **Dosage** (mg): Total drug dosage
- **Treatment Duration** (days): Length of treatment
- **Biomarker Level**: Relevant biomarker measurement
- **Liver Function Score** (0-1): Liver function assessment
- **Kidney Function Score** (0-1): Kidney function assessment

### Output
- **Prediction**: Binary classification (0=Not Effective, 1=Effective)
- **Probability**: Confidence score (0-1)
- **Confidence Level**: High/Medium/Low based on probability
- **Interpretation**: Human-readable explanation

## 📊 Monitoring

### System Metrics
- CPU Usage (%)
- Memory Usage (%)
- Disk Usage (%)
- Network I/O

### Application Metrics
- Request Count
- Response Time
- Prediction Count
- Model Inference Time

### Accessing Metrics
- **Streamlit Dashboard**: Navigate to "Metrics Dashboard"
- **Prometheus Endpoint**: `http://your-app/metrics`
- **Health Check**: `http://your-app/api/health`

<!-- ## 🧪 Load Testing

### Using Locust

```bash
# Install Locust
pip install locust

# Run basic load test
locust -f locustfile.py --host=http://your-app-url

# Run automated test
locust -f locustfile.py \\
  --host=http://your-app-url \\
  --users=100 \\
  --spawn-rate=10 \\
  --run-time=10m \\
  --html=test_report.html
```

### Test Scenarios
- **Normal Users**: Realistic usage patterns
- **High Volume Users**: Stress testing with rapid requests
- **Light Users**: Browse-only behavior -->

## 🚀 Deployment Commands

### Build and Push Images
```bash
# Login to ACR
az acr login --name pharmlacr

# Build images
docker build -f docker/Dockerfile.fastapi -t pharmlacr.azurecr.io/pharma-fastapi:latest .
docker build -f docker/Dockerfile.streamlit -t pharmlacr.azurecr.io/pharma-streamlit:latest .

# Push images
docker push pharmlacr.azurecr.io/pharma-fastapi:latest
docker push pharmlacr.azurecr.io/pharma-streamlit:latest
```

### Deploy to Kubernetes
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n pharma-ml
kubectl get services -n pharma-ml
kubectl get ingress -n pharma-ml
```

## 🔍 Troubleshooting

### Common Issues

#### API Connection Failed
```bash
# Check pod status
kubectl get pods -n pharma-ml
kubectl logs deployment/fastapi-deployment -n pharma-ml

# Check service endpoints
kubectl get endpoints -n pharma-ml
```

#### Cosmos DB Connection Issues
```bash
# Verify secrets
kubectl get secret cosmos-secret -n pharma-ml -o yaml

# Check Cosmos DB firewall settings in Azure Portal
```

#### Image Pull Errors
```bash
# Check ACR permissions
az acr show --name pharmlacr --query id
az aks show --name pharma-aks --resource-group pharma-ml-rg --query identityProfile

# Attach ACR to AKS
az aks update -n pharma-aks -g pharma-ml-rg --attach-acr pharmlacr
```

### Monitoring Commands
```bash
# View logs
kubectl logs -f deployment/fastapi-deployment -n pharma-ml
kubectl logs -f deployment/streamlit-deployment -n pharma-ml

# Port forwarding for local access
kubectl port-forward service/fastapi-service 8000:8000 -n pharma-ml
kubectl port-forward service/streamlit-service 8501:8501 -n pharma-ml

# Resource usage
kubectl top pods -n pharma-ml
kubectl top nodes
```

## 📈 Performance Optimization

### Scaling Recommendations
- **CPU Usage > 70%**: Scale up pods
- **Memory Usage > 80%**: Increase memory limits
- **Response Time > 2s**: Add more replicas

### Cost Optimization
- Monitor resource utilization
- Optimize container resource requests/limits
