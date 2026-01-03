---
sidebar_position: 2
---

# Deployment Guide

Deploy LearnFlow from zero to production in ~10-15 minutes.

## Prerequisites

### Required Tools

- **Kubernetes cluster** (minikube, GKE, EKS, AKS)
- **kubectl** - Kubernetes CLI
- **helm** - Kubernetes package manager (v3.x)
- **docker** - Container runtime

### Verify Prerequisites

```bash
# Check kubectl
kubectl version --client

# Check helm
helm version

# Check docker
docker --version

# Verify cluster access
kubectl cluster-info
```

### Required Credentials

- **Anthropic API Key**: Get from https://console.anthropic.com/
- **JWT Secret**: Generate a secure random string (min 32 characters)

```bash
# Generate JWT secret
openssl rand -base64 32
```

## One-Command Deployment

### Step 1: Set Environment Variables

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export JWT_SECRET="your-secret-key-minimum-32-characters"
```

### Step 2: Run Deployment Script

```bash
cd skills-library/learnflow-deploy
./scripts/deploy.sh
```

That's it! The script handles everything:

1. ✅ Validates prerequisites
2. ✅ Deploys PostgreSQL with schema
3. ✅ Deploys Kafka with topics
4. ✅ Installs Dapr runtime
5. ✅ Builds Docker images
6. ✅ Deploys all services
7. ✅ Runs health checks
8. ✅ Displays access URLs

### Step 3: Access LearnFlow

After deployment completes (~10-15 minutes):

```bash
# API Documentation
open https://learnflow.local/docs

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

## Manual Deployment

For learning or customization, follow these steps:

### 1. Create Namespace

```bash
kubectl create namespace learnflow
```

### 2. Create Secrets

```bash
# Anthropic API key
kubectl create secret generic anthropic-api-key \
  --from-literal=api-key=$ANTHROPIC_API_KEY \
  -n learnflow

# JWT secret
kubectl create secret generic jwt-secret \
  --from-literal=secret=$JWT_SECRET \
  -n learnflow
```

### 3. Deploy Infrastructure

#### PostgreSQL

```bash
cd skills-library/postgres-k8s-setup
./scripts/deploy.sh --namespace learnflow
```

#### Kafka

```bash
cd skills-library/kafka-k8s-setup
./scripts/deploy.sh --namespace learnflow
```

#### Dapr

```bash
helm repo add dapr https://dapr.github.io/helm-charts/
helm install dapr dapr/dapr --namespace dapr-system --create-namespace
```

### 4. Configure Dapr Components

```bash
# Pub/Sub (Kafka)
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

# State Store (PostgreSQL)
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

### 5. Build Docker Images

```bash
cd learnflow-app

# Build all images
docker build -t learnflow-api:latest -f docker/Dockerfile.api .
docker build -t learnflow-agents:latest -f docker/Dockerfile.agents .
docker build -t learnflow-sandbox:latest -f docker/Dockerfile.sandbox .
docker build -t learnflow-mcp:latest -f docker/Dockerfile.mcp .

# For minikube: Load images
minikube image load learnflow-api:latest
minikube image load learnflow-agents:latest
minikube image load learnflow-sandbox:latest
minikube image load learnflow-mcp:latest
```

### 6. Deploy with Helm

```bash
helm install learnflow ./helm/learnflow \
  --namespace learnflow \
  --set namespace=learnflow \
  --set domain=learnflow.local \
  --set replicas=3 \
  --wait
```

### 7. Run Database Migrations

```bash
kubectl exec -n learnflow deploy/learnflow-api -- \
  alembic upgrade head
```

### 8. Verify Deployment

```bash
# Check all pods
kubectl get pods -n learnflow

# Expected output:
# NAME                               READY   STATUS    RESTARTS
# learnflow-api-xxx                  2/2     Running   0
# learnflow-agents-xxx               2/2     Running   0
# learnflow-sandbox-xxx              2/2     Running   0
# learnflow-mcp-xxx                  2/2     Running   0
# postgres-xxx                       1/1     Running   0
# kafka-xxx                          1/1     Running   0

# Test health endpoints
kubectl port-forward -n learnflow svc/learnflow-api 8000:8000 &
curl http://localhost:8000/health
```

## Configuration Options

### Deployment Script Flags

```bash
./scripts/deploy.sh [OPTIONS]

Options:
  --namespace NAMESPACE   Kubernetes namespace (default: learnflow)
  --domain DOMAIN        Domain name (default: learnflow.local)
  --replicas N           API replicas (default: 3)
  --monitoring          Enable Prometheus monitoring
```

### Helm Values

Customize `helm/learnflow/values.yaml`:

```yaml
namespace: learnflow
domain: learnflow.local
replicas: 3

api:
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"

agents:
  replicas: 2
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
```

## Post-Deployment

### Test Demo Scenario

```bash
# Login as student
curl -X POST https://learnflow.local/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student@learnflow.com","password":"student123"}'

# Get token from response
TOKEN="<access_token>"

# Chat with AI tutor via WebSocket
wscat -c "wss://learnflow.local/api/v1/chat/ws?student_id=test-123" \
  -H "Authorization: Bearer $TOKEN"

# Send message
> {"type": "message", "content": "How do for loops work?"}
```

### Monitor Logs

```bash
# API logs
kubectl logs -n learnflow -l app=learnflow-api -f

# Agent logs
kubectl logs -n learnflow -l app=learnflow-agents -f

# All logs
kubectl logs -n learnflow --all-containers=true -f
```

### View Metrics

```bash
# Port forward Prometheus
kubectl port-forward -n learnflow svc/prometheus 9090:9090 &

# Open in browser
open http://localhost:9090
```

## Cleanup

Remove all LearnFlow resources:

```bash
# Uninstall Helm release
helm uninstall learnflow -n learnflow

# Delete namespace
kubectl delete namespace learnflow

# Remove Dapr (optional)
helm uninstall dapr -n dapr-system
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod
kubectl describe pod -n learnflow <pod-name>

# Check events
kubectl get events -n learnflow --sort-by='.lastTimestamp'
```

### Database Connection Failed

```bash
# Test PostgreSQL
kubectl exec -n learnflow deploy/postgres -- psql -U learnflow -c "SELECT 1"

# Check connection string
kubectl get secret -n learnflow postgres-secret -o yaml
```

### Dapr Sidecar Issues

```bash
# Check Dapr logs
kubectl logs -n learnflow <pod-name> -c daprd

# Verify Dapr components
kubectl get components -n learnflow
```

## Production Considerations

### High Availability

- Use managed Kubernetes (GKE, EKS, AKS)
- Deploy across multiple availability zones
- Configure pod disruption budgets
- Set up cluster autoscaling

### Security

- Enable TLS/SSL with cert-manager
- Use Kubernetes RBAC
- Store secrets in HashiCorp Vault
- Enable network policies
- Regular security scanning

### Monitoring

- Set up Prometheus + Grafana
- Configure alerting rules
- Enable distributed tracing
- Implement log aggregation (ELK stack)

### Backup

- Automated PostgreSQL backups
- Kafka topic snapshots
- Configuration backups

## Next Steps

1. [Explore the Architecture](./architecture)
2. [Learn about AI Agents](./agents)
3. [Read the API Documentation](./api)
4. [Review the Database Schema](./database)
