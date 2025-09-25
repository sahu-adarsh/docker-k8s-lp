#!/bin/bash

echo "🧪 Testing Todo API..."

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s http://localhost:8080/health | jq .

echo -e "\n2. Testing GET /api/todos (should be empty initially)..."
curl -s http://localhost:8080/api/todos | jq .

echo -e "\n3. Creating a new todo..."
curl -s -X POST http://localhost:8080/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Kubernetes"}' | jq .

echo -e "\n4. Creating another todo..."
curl -s -X POST http://localhost:8080/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Deploy with Docker"}' | jq .

echo -e "\n5. Getting all todos..."
curl -s http://localhost:8080/api/todos | jq .

echo -e "\n6. Updating first todo to completed..."
curl -s -X PUT http://localhost:8080/api/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn Kubernetes", "completed": true}' | jq .

echo -e "\n7. Getting updated todos..."
curl -s http://localhost:8080/api/todos | jq .

echo -e "\n8. Deleting second todo..."
curl -s -X DELETE http://localhost:8080/api/todos/2

echo -e "\n9. Final todos list..."
curl -s http://localhost:8080/api/todos | jq .

echo -e "\n✅ API testing completed!"

