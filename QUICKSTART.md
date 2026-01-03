# LearnFlow Quick Start Guide

## Prerequisites

1. **Kubernetes Cluster** (minikube, kind, GKE, EKS, or AKS)
   ```bash
   # For local testing with minikube:
   minikube start --memory=8192 --cpus=4
   ```

2. **Required Tools**
   ```bash
   # Check installations
   kubectl version --client
   helm version
   docker --version
   ```

3. **Anthropic API Key**
   - Sign up at https://console.anthropic.com/
   - Create an API key
   - Export it: `export ANTHROPIC_API_KEY="sk-ant-..."`

## Option 1: Autonomous Deployment (Recommended for Hackathon Demo)

### Single Command Deployment

```bash
# 1. Set environment variables
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export JWT_SECRET="your-secret-key-minimum-32-characters-long"

# 2. Navigate to deployment skill
cd ../skills-library/learnflow-deploy

# 3. Run autonomous deployment
./scripts/deploy.sh --namespace learnflow --domain learnflow.local --replicas 3

# ⏰ Wait ~10-15 minutes for complete deployment
```

That's it! The script will:
- ✅ Validate prerequisites
- ✅ Deploy PostgreSQL with schema
- ✅ Deploy Kafka with topics
- ✅ Install Dapr runtime
- ✅ Build Docker images
- ✅ Deploy all LearnFlow services
- ✅ Run health checks
- ✅ Display access URLs

### Access the Platform

After deployment completes:

```bash
# API Documentation
https://learnflow.local/docs

# Health Check
curl https://learnflow.local/api/v1/health

# Test Login
curl -X POST https://learnflow.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@learnflow.com",
    "password": "student123"
  }'
```

### Test WebSocket Chat

```bash
# Install wscat
npm install -g wscat

# Connect to chat
wscat -c "wss://learnflow.local/api/v1/chat/ws?student_id=test-123"

# Send message
> {"type": "message", "content": "How do for loops work?"}

# Receive AI tutor response
< {"type": "agent_response", "agent": "concepts", "content": "..."}
```

## Option 2: Manual Step-by-Step (For Learning)

### Step 1: Deploy Infrastructure

```bash
# PostgreSQL
cd ../skills-library/postgres-k8s-setup
./scripts/deploy.sh --namespace learnflow

# Kafka
cd ../kafka-k8s-setup
./scripts/deploy.sh --namespace learnflow

# Dapr
helm repo add dapr https://dapr.github.io/helm-charts/
helm install dapr dapr/dapr --namespace dapr-system --create-namespace
```

### Step 2: Create Namespace and Secrets

```bash
kubectl create namespace learnflow

kubectl create secret generic anthropic-api-key \
  --from-literal=api-key=$ANTHROPIC_API_KEY \
  -n learnflow

kubectl create secret generic jwt-secret \
  --from-literal=secret=$JWT_SECRET \
  -n learnflow
```

### Step 3: Configure Dapr Components

```bash
# Apply Dapr pub/sub component
kubectl apply -f - <<EOF
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kafka-pubsub
  namespace: learnflow
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka.learnflow.svc:9092"
  - name: consumerGroup
    value: "learnflow-group"
EOF

# Apply Dapr state store component
kubectl apply -f - <<EOF
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: postgres-state
  namespace: learnflow
spec:
  type: state.postgresql
  version: v1
  metadata:
  - name: connectionString
    value: "host=postgres.learnflow.svc user=learnflow password=learnflow123 port=5432 database=learnflow"
EOF
```

### Step 4: Build Docker Images

```bash
cd ../../learnflow-app

# Build all images
docker build -t learnflow-api:latest -f docker/Dockerfile.api .
docker build -t learnflow-agents:latest -f docker/Dockerfile.agents .
docker build -t learnflow-sandbox:latest -f docker/Dockerfile.sandbox .
docker build -t learnflow-mcp:latest -f docker/Dockerfile.mcp .

# For minikube: Load images into cluster
minikube image load learnflow-api:latest
minikube image load learnflow-agents:latest
minikube image load learnflow-sandbox:latest
minikube image load learnflow-mcp:latest
```

### Step 5: Deploy with Helm

```bash
helm install learnflow ./helm/learnflow \
  --namespace learnflow \
  --set namespace=learnflow \
  --set domain=learnflow.local \
  --set replicas=3 \
  --wait
```

### Step 6: Run Database Migrations

```bash
kubectl exec -n learnflow deploy/learnflow-api -- \
  alembic upgrade head
```

### Step 7: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n learnflow

# Check services
kubectl get svc -n learnflow

# Check ingress
kubectl get ingress -n learnflow

# Test API health
kubectl port-forward -n learnflow svc/learnflow-api 8000:8000 &
curl http://localhost:8000/health
```

## Testing the Multi-Agent System

### Test Each Agent

```bash
# Get API pod name
API_POD=$(kubectl get pod -n learnflow -l app=learnflow-api -o jsonpath='{.items[0].metadata.name}')

# Test Concepts Agent
kubectl exec -n learnflow $API_POD -- curl -X POST \
  http://learnflow-agents:8001/agents/concepts \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test-123",
    "message": "How do for loops work?",
    "context": {"student_level": "beginner"}
  }'

# Test Code Review Agent
kubectl exec -n learnflow $API_POD -- curl -X POST \
  http://learnflow-agents:8001/agents/code-review \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test-123",
    "message": "Review this code",
    "context": {
      "code": "for i in range(5):\n    print(i)"
    }
  }'

# Test Debug Agent
kubectl exec -n learnflow $API_POD -- curl -X POST \
  http://learnflow-agents:8001/agents/debug \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test-123",
    "message": "Help me fix this",
    "context": {
      "code": "print(x)",
      "error": "NameError: name '\''x'\'' is not defined"
    }
  }'
```

### Test MCP Server

```bash
# Get MCP pod
MCP_POD=$(kubectl get pod -n learnflow -l app=learnflow-mcp -o jsonpath='{.items[0].metadata.name}')

# Test MCP tools
kubectl exec -n learnflow $MCP_POD -- python -c "
import asyncio
from src.mcp_server.server import get_student_progress
result = asyncio.run(get_student_progress('test-123'))
print(result)
"
```

## Demo Scenario (From Specification)

### Student Maya's Journey

```bash
# 1. Login as student
TOKEN=$(curl -s -X POST https://learnflow.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@learnflow.com","password":"student123"}' \
  | jq -r '.access_token')

# 2. Check dashboard
curl -H "Authorization: Bearer $TOKEN" \
  https://learnflow.local/api/v1/students/me/dashboard

# 3. Connect to WebSocket and ask about for loops
wscat -c "wss://learnflow.local/api/v1/chat/ws?student_id=student-123" \
  -H "Authorization: Bearer $TOKEN"

> {"type": "message", "content": "How do for loops work in Python?"}

# 4. Get concept explanation from Concepts Agent
# Response: Detailed explanation with examples...

# 5. Submit code for review
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://learnflow.local/api/v1/code/execute \
  -d '{"code": "for i in range(5):\n    print(i)"}'

# 6. Check progress
curl -H "Authorization: Bearer $TOKEN" \
  https://learnflow.local/api/v1/progress/student-123
```

### Teacher Mr. Rodriguez

```bash
# 1. Login as teacher
TEACHER_TOKEN=$(curl -s -X POST https://learnflow.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teacher@learnflow.com","password":"teacher123"}' \
  | jq -r '.access_token')

# 2. View class performance
curl -H "Authorization: Bearer $TEACHER_TOKEN" \
  https://learnflow.local/api/v1/teachers/classes/1/performance

# 3. Check struggle alerts
curl -H "Authorization: Bearer $TEACHER_TOKEN" \
  https://learnflow.local/api/v1/teachers/struggle-alerts

# 4. Generate custom exercises
curl -X POST -H "Authorization: Bearer $TEACHER_TOKEN" \
  https://learnflow.local/api/v1/exercises/generate \
  -d '{"topic_id": 3, "difficulty": "easy"}'
```

## Monitoring

### View Logs

```bash
# API logs
kubectl logs -n learnflow -l app=learnflow-api -f

# Agent orchestrator logs
kubectl logs -n learnflow -l app=learnflow-agents -f

# Specific agent invocations
kubectl logs -n learnflow -l app=learnflow-agents | grep "Agent invocation"
```

### Prometheus Metrics

```bash
# Port forward Prometheus (if monitoring enabled)
kubectl port-forward -n learnflow svc/prometheus 9090:9090 &

# Open browser
open http://localhost:9090

# Example queries:
# - learnflow_api_requests_total
# - learnflow_agent_response_time_seconds
# - learnflow_websocket_connections_total
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod
kubectl describe pod -n learnflow <pod-name>

# Check events
kubectl get events -n learnflow --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
kubectl exec -n learnflow deploy/learnflow-api -- \
  psql postgresql://learnflow:learnflow123@postgres:5432/learnflow -c "SELECT 1"
```

### Anthropic API Errors

```bash
# Verify API key
kubectl get secret -n learnflow anthropic-api-key -o jsonpath='{.data.api-key}' | base64 -d

# Test Claude API
kubectl exec -n learnflow deploy/learnflow-agents -- python -c "
import anthropic
client = anthropic.Anthropic()
print(client.models.list())
"
```

### Dapr Issues

```bash
# Check Dapr sidecars
kubectl get pods -n learnflow -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}'

# Dapr logs
kubectl logs -n learnflow <pod-name> -c daprd
```

## Cleanup

```bash
# Remove LearnFlow
helm uninstall learnflow -n learnflow

# Remove infrastructure
kubectl delete namespace learnflow

# Remove Dapr
helm uninstall dapr -n dapr-system
```

## Next Steps

1. **Explore API Documentation**: https://learnflow.local/docs
2. **Read Architecture**: `docs/ARCHITECTURE.md`
3. **Understand Agents**: `AGENTS.md`
4. **Review Database Schema**: `docs/DATABASE_SCHEMA.md`
5. **Check Implementation**: `IMPLEMENTATION_SUMMARY.md`

## Support

- **Issues**: Check pod logs and events
- **Documentation**: See `/docs` directory
- **Health Checks**: `curl https://learnflow.local/health`
