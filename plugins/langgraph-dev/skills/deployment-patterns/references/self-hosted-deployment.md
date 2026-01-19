# Self-Hosted Deployment

Comprehensive guide to deploying LangGraph Platform in your own cloud environment with full control over infrastructure.

## Overview

Self-hosted deployment allows running all LangGraph Platform components entirely within your own cloud environment. Two deployment models are available:

1. **Standalone Server**: Deploy LangGraph Servers without control plane UI (data plane only)
2. **Full Platform**: Deploy both control plane and data plane with full UI/API management capabilities

**Requirements**: Self-hosted deployment requires an Enterprise plan. License key obtained from LangChain.

**Architecture Components**:
- **Control Plane**: UI and APIs for creating deployments and revisions
- **Data Plane**: LangGraph Servers, Postgres, Redis, background task queue
- **Infrastructure**: Kubernetes (production) or Docker/Docker Compose (development)

---

## Deployment Models Comparison

### Model 1: Standalone Server

**What it is**: Simplified deployment with data plane only, no control plane UI

**Architecture**:
- LangGraph Servers (stateless instances)
- PostgreSQL (persistent state, threads, runs)
- Redis (pub-sub broker for streaming)

**Where hosted**: Your cloud (you manage everything)

**Use cases**:
- Production deployments without UI management
- Maximum control and flexibility
- Custom infrastructure requirements
- Air-gapped environments

**Compute platforms**:
- Kubernetes (production)
- Docker (development/testing)
- Docker Compose (local development)

### Model 2: Full Platform

**What it is**: Complete deployment with control plane UI and data plane infrastructure

**Architecture**:
- Control Plane: UI/APIs for deployment management, hosted in your cloud
- Data Plane: LangGraph Servers, Postgres, Redis, listener (reconciler), hosted in your cloud

**Where hosted**: Your cloud (you manage both planes)

**Use cases**:
- Teams needing UI for deployment management
- Multi-deployment environments
- Enterprise deployments with governance

**Compute platforms**:
- Kubernetes only (with KEDA autoscaling)

**Prerequisites**:
- Self-hosted LangSmith instance deployed
- Kubernetes with Ingress configured
- KEDA installed for autoscaling

---

## Standalone Server Deployment

### Docker Compose (Development)

**When to use**: Local development, testing, proof-of-concept

**Docker Compose Configuration**:

```yaml
volumes:
    langgraph-data:
        driver: local

services:
    langgraph-redis:
        image: redis:6
        healthcheck:
            test: redis-cli ping
            interval: 5s
            timeout: 1s
            retries: 5

    langgraph-postgres:
        image: postgres:16
        ports:
            - "5432:5432"
        environment:
            POSTGRES_DB: postgres
            POSTGRES_USER: postgres
            POSTGRES_PASSWORD: postgres
        volumes:
            - langgraph-data:/var/lib/postgresql/data
        healthcheck:
            test: pg_isready -U postgres
            start_period: 10s
            timeout: 1s
            retries: 5
            interval: 5s

    langgraph-api:
        image: ${IMAGE_NAME}
        ports:
            - "8123:8000"
        depends_on:
            langgraph-redis:
                condition: service_healthy
            langgraph-postgres:
                condition: service_healthy
        env_file:
            - .env
        environment:
            REDIS_URI: redis://langgraph-redis:6379
            LANGSMITH_API_KEY: ${LANGSMITH_API_KEY}
            DATABASE_URI: postgres://postgres:postgres@langgraph-postgres:5432/postgres?sslmode=disable
```

**Environment Variables** (`.env` file):

```bash
IMAGE_NAME=my-langgraph-app:latest
LANGSMITH_API_KEY=lsv2_pt_...
LANGGRAPH_CLOUD_LICENSE_KEY=...
```

**Start Services**:

```bash
# Build image first
langgraph build -t my-langgraph-app:latest

# Start all services
docker compose up

# Verify health
curl --request GET --url 0.0.0.0:8123/ok
# Expected: {"ok":true}
```

**Features**:
- Single-command startup
- Automatic service dependencies (healthchecks)
- Persistent data (volume `langgraph-data`)
- Local port 8123 for API access

### Docker (Simple Deployment)

**When to use**: Single-container deployment, custom orchestration

**Command**:

```bash
docker run \
    --env-file .env \
    -p 8123:8000 \
    -e REDIS_URI="redis://my-redis-host:6379" \
    -e DATABASE_URI="postgres://user:pass@my-postgres-host:5432/langgraph?sslmode=require" \
    -e LANGSMITH_API_KEY="lsv2_pt_..." \
    -e LANGGRAPH_CLOUD_LICENSE_KEY="..." \
    my-langgraph-app:latest
```

**Requirements**:
- External Redis instance accessible
- External PostgreSQL instance accessible
- Image built with `langgraph build`

**Limitations**:
- No automatic Redis/Postgres provisioning
- Manual service management
- No built-in healthchecks

### Kubernetes + Helm (Production)

**When to use**: Production deployments, horizontal scaling, high availability

**Helm Chart**: https://github.com/langchain-ai/helm/blob/main/charts/langgraph-cloud/README.md

**Installation**:

```bash
# Add Helm repository
helm repo add langchain https://langchain-ai.github.io/helm
helm repo update

# Install chart
helm install my-langgraph langchain/langgraph-cloud \
    --set image.repository=my-registry/my-langgraph-app \
    --set image.tag=latest \
    --set env.REDIS_URI="redis://my-redis:6379" \
    --set env.DATABASE_URI="postgres://user:pass@my-postgres:5432/langgraph" \
    --set env.LANGSMITH_API_KEY="lsv2_pt_..." \
    --set env.LANGGRAPH_CLOUD_LICENSE_KEY="..." \
    --namespace langgraph \
    --create-namespace
```

**Custom Values** (`values.yaml`):

```yaml
replicaCount: 3

image:
  repository: my-registry/my-langgraph-app
  tag: "v1.2.3"
  pullPolicy: IfNotPresent

env:
  REDIS_URI: "redis://my-redis-cluster:6379"
  DATABASE_URI: "postgres://user:pass@my-postgres:5432/langgraph?sslmode=require"
  LANGSMITH_API_KEY: "lsv2_pt_..."
  LANGGRAPH_CLOUD_LICENSE_KEY: "..."
  N_JOBS_PER_WORKER: "20"
  LOG_LEVEL: "INFO"

resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: langgraph.example.com
      paths:
        - path: /
          pathType: Prefix
```

**Apply Custom Configuration**:

```bash
helm install my-langgraph langchain/langgraph-cloud \
    -f values.yaml \
    --namespace langgraph
```

**Features**:
- Horizontal autoscaling (HPA)
- Load balancing (via Ingress)
- Rolling updates
- Health checks (liveness, readiness)
- Resource limits and requests

---

## Full Platform Deployment

### Prerequisites

**Required**:
1. Kubernetes cluster with KEDA installed
2. Self-hosted LangSmith instance deployed
3. Ingress configured for LangSmith
4. Cluster autoscaler (recommended)
5. Dynamic PV provisioner

**Install KEDA** (Kubernetes Event Driven Autoscaling):

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm install keda kedacore/keda --namespace keda --create-namespace
```

**Verify Storage Class**:

```bash
kubectl get storageclass
# Should show available storage classes
```

### Configuration

**LangSmith Configuration** (`langsmith_config.yaml`):

```yaml
config:
  langgraphPlatform:
    enabled: true
    langgraphPlatformLicenseKey: "YOUR_LANGGRAPH_PLATFORM_LICENSE_KEY"
```

**Image Configuration** (`values.yaml`):

```yaml
hostBackendImage:
  repository: "docker.io/langchain/hosted-langserve-backend"
  pullPolicy: IfNotPresent

operatorImage:
  repository: "docker.io/langchain/langgraph-operator"
  pullPolicy: IfNotPresent
```

### Components Provisioned

**Control Plane**:
- `host-backend`: Control plane UI and APIs
- `listener`: Listens to control plane for deployment changes
- `operator`: Manages LangGraphPlatform CRDs

**Data Plane**:
- LangGraph Servers (deployed via CRDs)
- PostgreSQL instances (per deployment)
- Redis instances (per deployment)

**Workflow**:
1. Create deployment via control plane UI
2. Listener detects change and creates LangGraphPlatform CRD
3. Operator reconciles CRD and provisions data plane resources
4. LangGraph Server starts with specified image

---

## PostgreSQL Configuration

### Connection URI Format

```
postgres://<user>:<password>@<hostname>:<port>/<database>?sslmode=<mode>
```

**Example**:
```
postgres://langgraph_user:secure_password@my-postgres.example.com:5432/langgraph_db?sslmode=require
```

**SSL Modes**:
- `disable`: No SSL (development only)
- `require`: SSL required (production recommended)
- `verify-ca`: Verify CA certificate
- `verify-full`: Verify CA and hostname

### Version Requirements

- **Minimum Version**: PostgreSQL 15.8 or higher
- **Recommended**: PostgreSQL 16.x (latest stable)

### Shared Postgres Instance

**Multiple deployments can share one Postgres instance** using separate databases:

```bash
# Deployment A
DATABASE_URI=postgres://user:pass@shared-postgres:5432/deployment_a?sslmode=require

# Deployment B
DATABASE_URI=postgres://user:pass@shared-postgres:5432/deployment_b?sslmode=require
```

**CRITICAL**: Same database CANNOT be used for separate deployments (data corruption risk)

### Custom Postgres Instance

**Environment Variable**: `POSTGRES_URI_CUSTOM`

```bash
POSTGRES_URI_CUSTOM=postgres://user:pass@external-postgres:5432/langgraph?sslmode=require
```

**Control Plane Behavior**:
- Will NOT provision managed Postgres if `POSTGRES_URI_CUSTOM` set
- Will NOT delete external Postgres if deployment deleted
- Must ALWAYS be set once specified (cannot remove later)
- Can update URI (e.g., password rotation)

**User Responsibilities**:
- Ensure connectivity from LangGraph Server to Postgres
- Manage backups and replication
- Monitor performance and capacity
- Handle database migrations if needed

### Connection Pooling

**Environment Variable**: `LANGGRAPH_POSTGRES_POOL_MAX_SIZE`

```bash
# Default: 150 connections per replica
LANGGRAPH_POSTGRES_POOL_MAX_SIZE=150
```

**Calculation**:
```
Total Connections = Replicas × LANGGRAPH_POSTGRES_POOL_MAX_SIZE

Example: 10 replicas × 150 = 1,500 total connections
```

**Tuning Guidelines**:
- Start with default (150)
- Monitor connection usage
- Increase if seeing "connection pool exhausted" errors
- Decrease if Postgres max_connections limit reached
- Coordinate with Postgres `max_connections` setting

### Performance Tuning

**PostgreSQL Configuration**:

```
# postgresql.conf
max_connections = 2000  # Accommodate all replicas
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 16MB
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

**Best Practices**:
- Use connection pooling (PgBouncer) for large deployments
- Enable query logging for slow queries (> 100ms)
- Set up replication (streaming replication recommended)
- Configure automatic backups (WAL archiving + base backups)
- Monitor disk I/O and query performance

### Backup and Restore

**Backup Strategy**:

```bash
# Continuous archiving (WAL)
archive_mode = on
archive_command = 'cp %p /backup/wal/%f'

# Base backups (daily)
pg_basebackup -h localhost -U postgres -D /backup/base/$(date +%Y%m%d) -Fp -Xs -P
```

**Restore Procedure**:

```bash
# 1. Stop LangGraph Server
kubectl scale deployment langgraph-api --replicas=0

# 2. Restore base backup
pg_restore -h postgres-host -U postgres -d langgraph_db /backup/base/20260114

# 3. Replay WAL files if needed

# 4. Restart LangGraph Server
kubectl scale deployment langgraph-api --replicas=3
```

---

## Redis Configuration

### Connection URI Format

```
redis://<hostname>:<port>/<database_number>
```

**Example**:
```
redis://my-redis.example.com:6379/0
```

**With Authentication**:
```
redis://:password@my-redis.example.com:6379/0
```

### Redis Cluster Mode

**Environment Variable**: `REDIS_CLUSTER`

```bash
REDIS_CLUSTER=True
```

**When to use**: Connecting to Redis Cluster deployment (multi-node)

**Connection URI** (cluster mode):
```
redis://node1:6379,node2:6379,node3:6379/
```

### Shared Redis Instance

**Multiple deployments can share one Redis instance** using different database numbers:

```bash
# Deployment A (database 0)
REDIS_URI=redis://shared-redis:6379/0

# Deployment B (database 1)
REDIS_URI=redis://shared-redis:6379/1

# Deployment C (database 2)
REDIS_URI=redis://shared-redis:6379/2
```

**CRITICAL**: Same database number CANNOT be used for separate deployments

**Database Limits**: Redis supports 0-15 database numbers by default (16 databases)

### Custom Redis Instance

**Environment Variable**: `REDIS_URI_CUSTOM`

```bash
REDIS_URI_CUSTOM=redis://:password@external-redis:6379/0
```

**Similar control plane behavior as Postgres**:
- No managed Redis provisioned if set
- Not deleted on deployment removal
- Must remain set once specified

### Key Prefixing

**Environment Variable**: `REDIS_KEY_PREFIX`

```bash
REDIS_KEY_PREFIX=deployment_a_
```

**Use case**: Share single database with key isolation

**Example**:
```bash
# Deployment A
REDIS_URI=redis://shared-redis:6379/0
REDIS_KEY_PREFIX=app_a_

# Deployment B
REDIS_URI=redis://shared-redis:6379/0
REDIS_KEY_PREFIX=app_b_
```

**Keys stored**:
- Deployment A: `app_a_thread:123`, `app_a_run:456`
- Deployment B: `app_b_thread:789`, `app_b_run:012`

### High Availability

**Redis Sentinel** (recommended for production):

```bash
# Master-slave replication with automatic failover
redis-sentinel /etc/redis/sentinel.conf
```

**Sentinel Configuration**:

```
sentinel monitor langgraph-redis redis-master 6379 2
sentinel down-after-milliseconds langgraph-redis 5000
sentinel parallel-syncs langgraph-redis 1
sentinel failover-timeout langgraph-redis 10000
```

**Connection URI** (with Sentinel):
```
redis-sentinel://sentinel-host:26379/langgraph-redis/0
```

### Performance Tuning

**Redis Configuration**:

```
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

**Best Practices**:
- Monitor memory usage (set maxmemory)
- Use LRU eviction policy (allkeys-lru)
- Enable persistence (RDB snapshots + AOF)
- Configure replication for high availability
- Monitor connection count and latency

### TTL Configuration

**Resumable Streams**:

```bash
RESUMABLE_STREAM_TTL_SECONDS=120
```

**Use case**: Time-to-live for resumable stream data stored in Redis

**Default**: 120 seconds

---

## Environment Variables

### Required Variables

**Always Required**:

```bash
REDIS_URI=redis://my-redis:6379/0
DATABASE_URI=postgres://user:pass@my-postgres:5432/langgraph?sslmode=require
LANGSMITH_API_KEY=lsv2_pt_...
LANGGRAPH_CLOUD_LICENSE_KEY=...
```

### Authentication

**LangSmith Tracing**:

```bash
LANGSMITH_API_KEY=lsv2_pt_...          # LangSmith API key
LANGSMITH_TRACING=true                 # Enable tracing (default)
LANGSMITH_TRACING_SAMPLING_RATE=1.0    # Sample 100% of traces
```

**Self-Hosted LangSmith**:

```bash
LANGSMITH_ENDPOINT=https://my-langsmith.example.com
LANGSMITH_RUNS_ENDPOINTS='{"my-langsmith.example.com":"lsv2_pt_..."}'
```

**Authentication Type**:

```bash
LANGGRAPH_AUTH_TYPE=noop  # For self-hosted (no LangGraph Platform auth)
```

### Performance Tuning

**Background Jobs**:

```bash
N_JOBS_PER_WORKER=10                    # Jobs per worker (default: 10)
BG_JOB_TIMEOUT_SECS=3600                # Job timeout (default: 1 hour)
BG_JOB_SHUTDOWN_GRACE_PERIOD_SECS=180   # Shutdown grace period (default: 3 min)
BG_JOB_ISOLATED_LOOPS=True              # Isolate sync code (default: False)
```

**Connection Pooling**:

```bash
LANGGRAPH_POSTGRES_POOL_MAX_SIZE=150  # Max Postgres connections per replica
```

### Logging and Monitoring

**Log Configuration**:

```bash
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_JSON=true           # Output JSON logs (default: false)
LOG_COLOR=false         # Disable ANSI colors (default: true)
```

**Datadog Tracing**:

```bash
DD_API_KEY=...          # Datadog API key (enables ddtrace-run)
DD_SITE=datadoghq.com   # Datadog site
DD_ENV=production       # Environment tag
DD_SERVICE=langgraph    # Service name
DD_TRACE_ENABLED=true   # Enable tracing
```

### Advanced Configuration

**Mount Prefix** (self-hosted only):

```bash
MOUNT_PREFIX=/langgraph  # Serve under /langgraph path
```

**Redis Cluster**:

```bash
REDIS_CLUSTER=True      # Enable Redis Cluster mode
REDIS_KEY_PREFIX=app_   # Key prefix for isolation
```

**Custom Resources**:

```bash
POSTGRES_URI_CUSTOM=postgres://...  # Custom Postgres instance
REDIS_URI_CUSTOM=redis://...        # Custom Redis instance
```

---

## Scaling Strategies

### Horizontal Scaling

**Increase Replicas**:

```bash
# Manual scaling
kubectl scale deployment langgraph-api --replicas=10

# Helm values.yaml
replicaCount: 10
```

**Auto-Scaling** (Horizontal Pod Autoscaler):

```yaml
# values.yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

**Throughput Calculation**:
```
Total Throughput = Replicas × N_JOBS_PER_WORKER

Example: 10 replicas × 20 jobs = 200 concurrent background runs
```

### Vertical Scaling

**Resource Requests/Limits**:

```yaml
# values.yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "4000m"
```

**Guidelines**:
- Start with 512Mi memory, 500m CPU
- Monitor actual usage with `kubectl top pods`
- Increase if seeing OOMKilled or CPU throttling
- Set limits 2-4× requests for burst capacity

### Database Scaling

**PostgreSQL Scaling**:
- Vertical: Increase instance size (CPU, RAM, disk)
- Horizontal: Read replicas (not for writes, LangGraph uses writes)
- Connection pooling: PgBouncer for connection management

**Redis Scaling**:
- Vertical: Increase memory
- Horizontal: Redis Cluster (sharding)
- Sentinel: High availability (failover)

### Load Balancing

**Ingress Configuration**:

```yaml
# values.yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
  hosts:
    - host: langgraph.example.com
      paths:
        - path: /
          pathType: Prefix
```

**Round-Robin Load Balancing**:
- Ingress controller distributes requests across replicas
- No session affinity needed (stateless servers)
- Any replica can handle any request

---

## Monitoring and Observability

### Health Checks

**Endpoint**: `GET /ok`

```bash
curl http://localhost:8123/ok
# Response: {"ok": true}
```

**Kubernetes Probes**:

```yaml
# Helm chart includes these by default
livenessProbe:
  httpGet:
    path: /ok
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ok
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Metrics

**Prometheus Integration**:

LangGraph Server exposes metrics at `/metrics` endpoint (if Prometheus instrumentation added).

**Key Metrics to Monitor**:
- `langgraph_active_runs`: Active background runs
- `langgraph_queued_runs`: Pending runs in queue
- `langgraph_request_duration_seconds`: API request latency
- `langgraph_postgres_connections`: Postgres connection pool usage
- `langgraph_redis_operations`: Redis operation count

**Grafana Dashboard**:
- Track run throughput over time
- Monitor queue depth
- Alert on queue buildup (> 100 pending)
- Alert on high latency (> 5s p95)

### Logging

**Structured Logging**:

```bash
LOG_JSON=true  # Enable JSON logs
LOG_LEVEL=INFO
```

**Log Aggregation** (example with Loki):

```yaml
# Kubernetes DaemonSet for log forwarding
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: promtail
spec:
  template:
    spec:
      containers:
      - name: promtail
        image: grafana/promtail:latest
        args:
        - -config.file=/etc/promtail/config.yml
```

**Log Queries**:
```
# Find errors
{namespace="langgraph"} |= "ERROR"

# Track specific run
{namespace="langgraph"} | json | run_id="abc123"
```

### Tracing

**LangSmith Integration** (automatic):

```bash
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_TRACING=true
```

**Datadog APM**:

```bash
DD_API_KEY=...
DD_SERVICE=langgraph
DD_ENV=production
DD_TRACE_ENABLED=true
```

**OpenTelemetry** (custom instrumentation):

```python
# Add to your graph code
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider()
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
```

---

## Security

### Network Security

**Egress Requirements**:

```bash
# License verification (unless air-gapped)
https://beacon.langchain.com

# LangSmith tracing (if enabled)
https://api.smith.langchain.com
```

**Firewall Rules**:
- Allow egress to beacon.langchain.com (HTTPS/443)
- Allow egress to LangSmith endpoint (HTTPS/443)
- Allow internal communication: LangGraph ↔ Postgres, Redis

**Air-Gapped Mode**:
- Contact LangChain for air-gapped license
- Set `LANGSMITH_TRACING=false`
- No external egress required

### Secrets Management

**Kubernetes Secrets**:

```bash
# Create secret
kubectl create secret generic langgraph-secrets \
  --from-literal=LANGSMITH_API_KEY=lsv2_pt_... \
  --from-literal=LANGGRAPH_CLOUD_LICENSE_KEY=... \
  --from-literal=DATABASE_URI=postgres://... \
  --from-literal=REDIS_URI=redis://... \
  --namespace langgraph

# Reference in Helm values
envFrom:
  - secretRef:
      name: langgraph-secrets
```

**External Secrets Operator** (recommended):

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: langgraph-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: langgraph-secrets
  data:
    - secretKey: LANGSMITH_API_KEY
      remoteRef:
        key: prod/langgraph/langsmith-api-key
```

### SSL/TLS

**Postgres SSL**:

```bash
DATABASE_URI=postgres://user:pass@host:5432/db?sslmode=require
```

**Ingress TLS**:

```yaml
# values.yaml
ingress:
  enabled: true
  tls:
    - secretName: langgraph-tls
      hosts:
        - langgraph.example.com
```

**Certificate Management** (cert-manager):

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: langgraph-tls
spec:
  secretName: langgraph-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - langgraph.example.com
```

---

## Best Practices

### Infrastructure

1. **Use Kubernetes for production** - Docker Compose only for development
2. **Enable autoscaling** - HPA for pods, cluster autoscaler for nodes
3. **Provision excess capacity** - Start with 2× expected load
4. **Use managed services** - Managed Postgres/Redis when available
5. **Enable monitoring** - Prometheus, Grafana, log aggregation
6. **Implement backups** - Automated Postgres backups, WAL archiving

### Configuration

1. **Use Helm values files** - Version-controlled configuration
2. **Externalize secrets** - Kubernetes Secrets or External Secrets Operator
3. **Set resource limits** - Prevent resource exhaustion
4. **Configure health checks** - Liveness and readiness probes
5. **Enable structured logging** - JSON logs for parsing
6. **Tune connection pools** - Match Postgres max_connections

### Deployment

1. **Use rolling updates** - Zero-downtime deployments
2. **Test in staging** - Validate before production
3. **Monitor during rollout** - Watch error rates, latency
4. **Implement rollback plan** - `helm rollback` ready
5. **Document runbooks** - Incident response procedures

### Maintenance

1. **Regular updates** - Keep LangGraph Server image current
2. **Database maintenance** - VACUUM, REINDEX, statistics updates
3. **Monitor disk usage** - Postgres WAL, Redis memory
4. **Review logs** - Check for errors, warnings
5. **Test disaster recovery** - Practice backup/restore

---

## Troubleshooting

### Issue: Server Won't Start

**Symptoms**: Pods in CrashLoopBackOff

**Solutions**:
1. Check logs: `kubectl logs -n langgraph <pod-name>`
2. Verify environment variables are set correctly
3. Test connectivity to Postgres: `psql $DATABASE_URI`
4. Test connectivity to Redis: `redis-cli -u $REDIS_URI ping`
5. Verify license key is valid
6. Check egress to beacon.langchain.com (unless air-gapped)

### Issue: Connection Pool Exhausted

**Symptoms**: `connection pool exhausted` in logs

**Solutions**:
1. Increase `LANGGRAPH_POSTGRES_POOL_MAX_SIZE`
2. Increase Postgres `max_connections`
3. Reduce number of replicas temporarily
4. Add PgBouncer for connection pooling
5. Check for connection leaks in application code

### Issue: High Latency

**Symptoms**: API requests taking > 5 seconds

**Solutions**:
1. Check Postgres query performance (slow query log)
2. Monitor Redis latency: `redis-cli --latency`
3. Increase replica count (horizontal scaling)
4. Increase resource limits (vertical scaling)
5. Review graph code for inefficiencies
6. Check if `BG_JOB_ISOLATED_LOOPS=True` needed

### Issue: Background Runs Stuck in Pending

**Symptoms**: Runs stay in "pending" status

**Solutions**:
1. Check worker logs for errors
2. Verify Redis connection working
3. Increase `N_JOBS_PER_WORKER`
4. Add more replicas
5. Check `BG_JOB_TIMEOUT_SECS` not too low
6. Verify Postgres is not overloaded

### Issue: Pod Restarts

**Symptoms**: Frequent pod restarts, OOMKilled

**Solutions**:
1. Increase memory limits: `resources.limits.memory`
2. Check for memory leaks in application code
3. Monitor actual memory usage: `kubectl top pods`
4. Enable `BG_JOB_ISOLATED_LOOPS=True` if using sync code
5. Review `BG_JOB_SHUTDOWN_GRACE_PERIOD_SECS`

### Issue: License Errors

**Symptoms**: `License verification failed`

**Solutions**:
1. Verify `LANGGRAPH_CLOUD_LICENSE_KEY` is correct
2. Check egress to beacon.langchain.com allowed
3. For air-gapped: Verify air-gapped license obtained
4. Check license expiration date
5. Contact LangChain support for renewal

---

## Production Checklist

**Infrastructure**:
- [ ] Kubernetes cluster provisioned
- [ ] Managed Postgres (or self-hosted with backups)
- [ ] Managed Redis (or self-hosted with replication)
- [ ] Ingress controller configured
- [ ] TLS certificates provisioned (cert-manager)
- [ ] DNS records created

**Security**:
- [ ] Secrets managed externally (not in values.yaml)
- [ ] Postgres SSL enabled (`sslmode=require`)
- [ ] Network policies configured
- [ ] RBAC roles defined
- [ ] Egress firewall rules set

**Scaling**:
- [ ] Horizontal Pod Autoscaler configured
- [ ] Cluster autoscaler enabled
- [ ] Resource requests/limits set
- [ ] Connection pool sized appropriately

**Monitoring**:
- [ ] Prometheus metrics enabled
- [ ] Grafana dashboards created
- [ ] Log aggregation configured (Loki, ELK)
- [ ] Alerts configured (queue depth, error rate, latency)
- [ ] Tracing enabled (LangSmith or Datadog)

**Reliability**:
- [ ] Health checks configured (liveness, readiness)
- [ ] Postgres backups automated (daily base + continuous WAL)
- [ ] Redis persistence enabled (RDB + AOF)
- [ ] Disaster recovery tested
- [ ] Runbooks documented

**Deployment**:
- [ ] Helm chart values in version control
- [ ] CI/CD pipeline configured
- [ ] Staging environment tested
- [ ] Rollback procedure documented
- [ ] On-call rotation established

---

## References

- [Self-Hosted Overview](https://docs.langchain.com/langgraph-platform/self-hosted)
- [Deploy Standalone Server](https://docs.langchain.com/langgraph-platform/deploy-standalone-server)
- [Deploy Full Platform](https://docs.langchain.com/langgraph-platform/deploy-self-hosted-full-platform)
- [Environment Variables Reference](https://langchain-ai.github.io/langgraph/cloud/reference/env_var/)
- [Helm Chart Documentation](https://github.com/langchain-ai/helm/blob/main/charts/langgraph-cloud/README.md)
- [LangGraph CLI](https://langchain-ai.github.io/langgraph/cloud/reference/cli/)

---

**Created**: 2026-01-14
**LangGraph Platform Version**: Latest
**Status**: Active
