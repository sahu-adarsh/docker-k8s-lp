# Todo API with Database

A Node.js REST API for managing todos with PostgreSQL database, containerized with Docker and deployed on Kubernetes.

## Features

- ✅ CRUD operations for todos
- 🐘 PostgreSQL database with persistent storage
- 🐳 Docker containerization
- ☸️ Kubernetes deployment with ConfigMaps and Secrets
- 🔍 Health checks and monitoring
- 🔒 Security best practices

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /api/todos` - Get all todos
- `POST /api/todos` - Create a new todo
- `PUT /api/todos/:id` - Update a todo
- `DELETE /api/todos/:id` - Delete a todo

## Quick Start

### Prerequisites

- Docker
- Kubernetes cluster (minikube, kind, or cloud)
- kubectl

### Deploy to Kubernetes

**On Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**On Windows:**
```cmd
deploy.bat
```

### Test the API

1. Port forward the service:
```bash
kubectl port-forward -n todo-app service/todo-api-service 8080:80
```

2. Test the API:
```bash
# Health check
curl http://localhost:8080/health

# Get all todos
curl http://localhost:8080/api/todos

# Create a todo
curl -X POST http://localhost:8080/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Kubernetes"}'
```

### Run Tests

```bash
chmod +x test-api.sh
./test-api.sh
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Todo API      │    │   PostgreSQL    │
│   (Node.js)     │◄──►│   Database      │
│   Port: 3000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Kubernetes    │
│   Service       │
│   Port: 80      │
└─────────────────┘
```

## Kubernetes Resources

- **Namespace**: `todo-app`
- **PostgreSQL**: Deployment with PersistentVolumeClaim
- **Todo API**: Deployment with 2 replicas
- **ConfigMap**: Database configuration
- **Secret**: Database password
- **Service**: ClusterIP service for API access

## Learning Objectives

- ✅ Deploy databases with persistent storage
- ✅ Manage configuration with ConfigMaps and Secrets
- ✅ Implement service-to-service communication
- ✅ Handle stateful applications
- ✅ Use health checks and resource limits
