# Task Queues and Background Processing

Comprehensive guide to async execution, task queuing, and horizontal scaling on LangGraph Platform.

## Overview

LangGraph Platform provides robust infrastructure for background task processing with:
- **Task Queues**: Async job execution without blocking HTTP requests
- **Horizontal Scaling**: Stateless instances scale linearly with workload
- **Automatic Failover**: Crash resilience and exactly-once execution semantics
- **Concurrent Execution**: Configurable concurrency per instance

**Architecture**: Agent Server + Postgres + Redis + Task Queue

**Use Cases**:
- Long-running graph executions
- Batch processing
- High-throughput applications
- Async workflows
- Background jobs

---

## Background Runs

### Creating Background Runs

**Pattern**: Fire-and-forget execution, poll for completion

```python
from langgraph_sdk import get_client

client = get_client(url="<DEPLOYMENT_URL>")
thread = await client.threads.create()

# Start background run (non-blocking)
run = await client.runs.create(
    thread["thread_id"],
    "agent",
    input={"messages": [{"role": "user", "content": "Process this long task"}]}
)

print(f"Run started: {run['run_id']}")
print(f"Status: {run['status']}")  # "pending"
```

**Behavior**:
- Returns immediately with `status="pending"`
- Execution happens asynchronously in queue worker
- Client can check status later

### Polling for Completion

```python
# Check status
run_status = await client.runs.get(thread["thread_id"], run["run_id"])
print(run_status["status"])  # "pending", "running", "success", "error"

# Wait for completion (blocking)
await client.runs.join(thread["thread_id"], run["run_id"])

# Get final state
final_result = await client.threads.get_state(thread["thread_id"])
print(final_result["values"]["messages"][-1]["content"])
```

### Run Status Lifecycle

```
pending → running → success
                 → error
                 → cancelled
```

**Status Meanings**:
- `pending`: Queued, waiting for worker
- `running`: Currently executing
- `success`: Completed successfully
- `error`: Failed with error
- `cancelled`: User cancelled

---

## Concurrent Execution

### Multitask Strategies

**Problem**: Multiple runs submitted to same thread simultaneously (double-texting)

**Solutions**:

#### Strategy 1: Enqueue (Default)

**Behavior**: Queue runs, execute in order received

```python
# Start first run
first_run = await client.runs.create(
    thread["thread_id"],
    "agent",
    input={"messages": [{"role": "user", "content": "What's the weather in SF?"}]}
)

# Start second run (queued, waits for first to complete)
second_run = await client.runs.create(
    thread["thread_id"],
    "agent",
    input={"messages": [{"role": "user", "content": "What's the weather in NYC?"}]},
    multitask_strategy="enqueue"  # Default
)

# Wait for both to complete
await client.runs.join(thread["thread_id"], second_run["run_id"])

# Thread state includes results from both runs
state = await client.threads.get_state(thread["thread_id"])
```

**When to use**:
- Conversational agents (preserve turn order)
- Sequential dependencies
- State accumulation

#### Strategy 2: Reject

**Behavior**: Reject new run if one already running

```python
run1 = await client.runs.create(
    thread["thread_id"],
    "agent",
    input={...},
    multitask_strategy="reject"
)

# This will fail with HTTP 409 if run1 still running
try:
    run2 = await client.runs.create(
        thread["thread_id"],
        "agent",
        input={...},
        multitask_strategy="reject"
    )
except httpx.HTTPStatusError as e:
    if e.response.status_code == 409:
        print("Run already in progress")
```

**When to use**:
- Exclusive access required
- Prevent race conditions
- Resource-intensive operations

#### Strategy 3: Interrupt

**Behavior**: Cancel running run, start new one immediately

```python
run1 = await client.runs.create(
    thread["thread_id"],
    "agent",
    input={"messages": [{"role": "user", "content": "Long task..."}]}
)

# Cancel run1 and start run2
run2 = await client.runs.create(
    thread["thread_id"],
    "agent",
    input={"messages": [{"role": "user", "content": "Urgent! Cancel previous"}]},
    multitask_strategy="interrupt"
)

# run1 status will be "cancelled"
```

**When to use**:
- Latest input always most important
- Real-time correction/override
- User interruptions

---

## Horizontal Scaling

### Architecture Overview

**Stateless Instances**: Each Agent Server instance is stateless (no in-memory resources)

**Shared State**: All state in Postgres + Redis
- **Postgres**: Persistent data (checkpoints, threads, runs)
- **Redis**: Ephemeral metadata, cross-instance communication

**Load Balancing**: Instances share HTTP load (any strategy works, no session stickiness)

### Scaling HTTP Servers

**Adding Instances**:
```bash
# Start multiple instances (each listens on different port or behind load balancer)
langgraph up --port 8000  # Instance 1
langgraph up --port 8001  # Instance 2
langgraph up --port 8002  # Instance 3
```

**Load Balancer Configuration** (example: nginx):
```nginx
upstream langgraph_servers {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://langgraph_servers;
    }
}
```

**Behavior**:
- Requests distributed across instances
- Any instance can handle any request
- No sticky sessions needed

### Scaling Queue Workers

**Default Configuration**: Each instance handles 10 concurrent runs

**Calculating Throughput**:
```
Total Throughput = Instances × Concurrent Runs per Instance
Example: 5 instances × 10 runs = 50 concurrent runs
```

**Configuration** (langgraph.json):
```json
{
  "queue": {
    "enabled": true,
    "max_concurrent_runs": 10  // Per instance
  }
}
```

**Increasing Concurrency**:
```json
{
  "queue": {
    "enabled": true,
    "max_concurrent_runs": 20  // 2x throughput per instance
  }
}
```

**Scaling Considerations**:
- More instances = linear throughput increase
- More concurrent runs per instance = higher throughput, more resource usage
- Balance: instance count vs concurrency per instance

---

## Resilience

### Exactly-Once Execution

**Guarantee**: Each run attempt executed exactly once (no duplicates, no skips)

**Implementation**: Postgres MVCC (Multi-Version Concurrency Control)
- No long-lived transactions
- No locks
- Efficient resource usage

**Retry Logic**:
- Transient database errors → Retry up to 3 times
- Permanent errors → Run fails with error status

### Graceful Shutdown

**Behavior on SIGINT**:
```
1. Stop accepting new HTTP requests
2. Give in-progress runs limited time to finish
3. Unfinished runs re-queued for other instances
4. Stop picking up new runs from queue
```

**Example**:
```bash
# Send SIGINT
kill -SIGINT <PID>

# Instance gracefully shuts down
# In-progress runs complete or re-queue
# Other instances pick up re-queued runs
```

### Crash Resilience

**Hard Shutdown** (server crash, infrastructure failure):
```
1. In-progress runs lose heartbeat
2. Sweeper task detects missed heartbeats (every 2 minutes)
3. Sweeper re-queues abandoned runs
4. Other instances pick up and execute
```

**Heartbeat Mechanism**:
- Queue worker periodically updates timestamp in Redis
- Sweeper checks for runs with stale timestamps
- Automatic recovery without manual intervention

### Database Resilience

**Postgres** (Production deployments):
- Periodic backups
- Continuously replicated standby replicas
- Automatic failover
- Retries for retry-able errors

**Behavior**:
- Momentary unavailability (restart) → Traffic continues (with retries)
- Prolonged failure → Agent Server unavailable

**Redis**:
- Ephemeral metadata only (no durable requirements)
- Retries for retry-able errors
- Momentary unavailability → Traffic continues
- Prolonged failure → Agent Server unavailable

---

## Best Practices

### 1. Use Background Runs for Long Tasks

```python
# ❌ Bad - Blocks until completion
result = await client.runs.wait(thread["thread_id"], "agent", input={...})

# ✅ Good - Non-blocking
run = await client.runs.create(thread["thread_id"], "agent", input={...})
# Do other work...
await client.runs.join(thread["thread_id"], run["run_id"])  # Wait when needed
```

### 2. Poll Efficiently

```python
# ❌ Bad - Tight loop wastes resources
while True:
    status = await client.runs.get(thread["thread_id"], run["run_id"])
    if status["status"] in ["success", "error"]:
        break

# ✅ Good - Use join (blocks efficiently)
await client.runs.join(thread["thread_id"], run["run_id"])

# ✅ Good - Poll with backoff
import asyncio

async def wait_for_run(thread_id, run_id, timeout=300):
    start = asyncio.get_event_loop().time()
    delay = 1  # Start with 1 second

    while asyncio.get_event_loop().time() - start < timeout:
        status = await client.runs.get(thread_id, run_id)
        if status["status"] in ["success", "error", "cancelled"]:
            return status

        await asyncio.sleep(delay)
        delay = min(delay * 2, 30)  # Exponential backoff, max 30s

    raise TimeoutError("Run did not complete")
```

### 3. Handle Errors Gracefully

```python
run = await client.runs.create(thread["thread_id"], "agent", input={...})
await client.runs.join(thread["thread_id"], run["run_id"])

status = await client.runs.get(thread["thread_id"], run["run_id"])

if status["status"] == "error":
    error_msg = status.get("error", "Unknown error")
    print(f"Run failed: {error_msg}")
    # Handle error (retry, log, alert)
elif status["status"] == "success":
    # Process results
    state = await client.threads.get_state(thread["thread_id"])
```

### 4. Use Appropriate Multitask Strategy

```python
# Conversational agent - preserve order
await client.runs.create(
    thread["thread_id"],
    "chat_agent",
    input={...},
    multitask_strategy="enqueue"  # Default
)

# Real-time updates - latest always wins
await client.runs.create(
    thread["thread_id"],
    "dashboard_updater",
    input={...},
    multitask_strategy="interrupt"
)

# Critical operation - exclusive access
await client.runs.create(
    thread["thread_id"],
    "payment_processor",
    input={...},
    multitask_strategy="reject"
)
```

### 5. Monitor Queue Depth

```python
# Track pending runs
pending_runs = await client.runs.list(thread["thread_id"])
pending_count = sum(1 for r in pending_runs if r["status"] == "pending")

if pending_count > 10:
    print(f"Warning: {pending_count} runs queued, consider scaling")
```

---

## Configuration Reference

### langgraph.json Queue Settings

```json
{
  "queue": {
    "enabled": true,
    "max_concurrent_runs": 10
  },
  "http": {
    "timeout": 300  // Request timeout (seconds)
  }
}
```

**Options**:

| Setting | Default | Description |
|---------|---------|-------------|
| `queue.enabled` | `true` | Enable task queue |
| `queue.max_concurrent_runs` | `10` | Max concurrent runs per instance |
| `http.timeout` | `300` | HTTP request timeout (seconds) |

---

## Troubleshooting

### Issue: Runs Stuck in Pending

**Symptoms**: Runs stay in "pending" status indefinitely

**Solutions**:
1. Check queue workers are running: `ps aux | grep langgraph`
2. Check Redis connection: Is Redis accessible?
3. Check logs for errors: `docker logs <container>`
4. Increase queue workers: Add more instances

### Issue: Runs Failing with Timeout

**Symptoms**: Runs error with timeout message

**Solutions**:
1. Increase `http.timeout` in langgraph.json
2. Optimize graph execution (reduce LLM calls, parallelize)
3. Use async operations where possible

### Issue: Duplicate Executions

**Symptoms**: Same run executed multiple times

**Solutions**:
- **Should not happen** - Report bug if seen
- Check Postgres connection is stable
- Verify exactly-once semantics not violated

### Issue: Low Throughput

**Symptoms**: Runs process slowly despite low load

**Solutions**:
1. Increase `max_concurrent_runs` per instance
2. Add more instances (horizontal scaling)
3. Check Postgres query performance
4. Monitor Redis latency
5. Optimize graph node execution time

---

## Production Checklist

- [ ] **Queue Enabled**: `queue.enabled: true` in langgraph.json
- [ ] **Concurrency Tuned**: `max_concurrent_runs` set based on workload
- [ ] **Load Balancer**: Configured for HTTP instances
- [ ] **Monitoring**: Track queue depth, run status, throughput
- [ ] **Error Handling**: Application handles run failures gracefully
- [ ] **Scaling Strategy**: Plan for horizontal scaling (instances + concurrency)
- [ ] **Database**: Postgres configured for production (backups, replicas)
- [ ] **Redis**: Configured for high availability (replication)
- [ ] **Heartbeat Monitoring**: Verify sweeper task detecting abandoned runs

---

## References

- [Background Runs How-To](https://docs.langchain.com/langgraph-platform/background-run)
- [Enqueue Concurrent Runs](https://docs.langchain.com/langgraph-platform/enqueue-concurrent)
- [Scalability & Resilience](https://docs.langchain.com/langgraph-platform/scalability-and-resilience)
- [Agent Server Overview](https://docs.langchain.com/langsmith/agent-server)
- [Double-Texting Conceptual Guide](https://docs.langchain.com/langsmith/double-texting)

---

**Created**: 2026-01-14
**LangGraph Platform Version**: Latest
**Status**: Active
