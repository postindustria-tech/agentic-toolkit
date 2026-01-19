# Cron Jobs and Webhooks

Comprehensive guide to scheduled execution and event-driven invocation on LangGraph Platform.

## Overview

LangGraph Platform supports two patterns for automated and event-driven graph execution:

1. **Cron Jobs**: Scheduled execution at specific times (time-driven)
2. **Webhooks**: Event notifications to external services (event-driven)

**Requirements**:
- **Cron Jobs**: LangGraph API ≥0.5.18, Python SDK ≥0.3.2, or JS SDK ≥1.4.0
- **Webhooks**: LangGraph API ≥0.5.36 (for advanced features)

---

## Cron Jobs

### Concept

Cron jobs run assistants on a user-defined schedule, automatically creating threads and sending inputs at specified times.

**Use Cases**:
- Daily email summaries
- Weekly report generation
- Nightly data synchronization
- Periodic health checks
- Scheduled reminders

**How it works**:
1. User specifies: schedule (cron expression), assistant, input
2. On schedule: Server creates thread → Sends input → Runs assistant
3. Results: Stored in thread (or thread deleted if stateless + auto-cleanup)

### Cron Expression Syntax

**Format**: `minute hour day month weekday`

| Field | Range | Special Characters |
|-------|-------|-------------------|
| Minute | 0-59 | `*` `,` `-` `/` |
| Hour | 0-23 (24-hour) | `*` `,` `-` `/` |
| Day | 1-31 | `*` `,` `-` `/` |
| Month | 1-12 | `*` `,` `-` `/` |
| Weekday | 0-6 (Sun-Sat) | `*` `,` `-` `/` |

**Common Patterns**:
```
"0 9 * * *"       # Every day at 9:00 AM
"30 14 * * 1"     # Every Monday at 2:30 PM
"0 0 1 * *"       # First day of every month at midnight
"*/15 * * * *"    # Every 15 minutes
"0 */6 * * *"     # Every 6 hours
"0 0 * * 0"       # Every Sunday at midnight
"27 15 * * *"     # Every day at 3:27 PM
```

**Resources**: [Crontab Guru](https://crontab.cronhub.io/) for interactive expression building

### Creating Cron Jobs

#### Pattern 1: Thread-Based Cron (Stateful)

**When to use**: Multi-turn conversations where each execution builds on previous

```python
from langgraph_sdk import get_client

client = get_client(url="<DEPLOYMENT_URL>")

# Create thread for stateful conversation
thread = await client.threads.create()

# Create cron job on specific thread
cron_job = await client.crons.create_for_thread(
    thread["thread_id"],
    "agent",  # Assistant ID
    schedule="27 15 * * *",  # Every day at 3:27 PM
    input={"messages": [{"role": "user", "content": "Daily status update"}]}
)

print(f"Cron job ID: {cron_job['cron_id']}")
```

**Behavior**:
- Same thread used for every execution
- State persists between runs
- Context accumulates over time

**Use cases**:
- Ongoing conversations with memory
- Iterative refinement tasks
- Continuous monitoring with context

#### Pattern 2: Stateless Cron (New Thread Each Time)

**When to use**: Independent executions, no need for historical context

```python
# Create stateless cron (new thread per execution)
cron_job = await client.crons.create(
    "agent",  # Assistant ID
    schedule="0 9 * * *",  # Every day at 9:00 AM
    input={"messages": [{"role": "user", "content": "Generate daily report"}]}
)
```

**Behavior**:
- New thread created for each execution
- No state sharing between runs
- Each execution independent

### Thread Cleanup for Stateless Crons

**Problem**: Stateless crons create new threads each time → Thread accumulation

**Solution**: Configure cleanup behavior with `on_run_completed`

**Option 1: Auto-Delete (Default)**

```python
cron_job = await client.crons.create(
    "agent",
    schedule="0 0 * * *",  # Daily at midnight
    input={"messages": [{"role": "user", "content": "Daily task"}]},
    on_run_completed="delete"  # Auto-delete thread after run (default)
)
```

**Behavior**: Thread automatically deleted after run completes
**Use when**: Don't need to access run results later

**Option 2: Keep Threads**

```python
cron_job = await client.crons.create(
    "agent",
    schedule="0 */4 * * *",  # Every 4 hours
    input={"messages": [{"role": "user", "content": "Health check"}]},
    on_run_completed="keep"  # Keep thread for later retrieval
)

# Later: retrieve runs and results
runs = await client.runs.search(
    metadata={"cron_id": cron_job["cron_id"]}
)

for run in runs:
    print(f"Run at {run['created_at']}: {run['status']}")
```

**IMPORTANT**: If using `on_run_completed="keep"`, configure TTL in `langgraph.json` to prevent unbounded growth:

```json
{
  "checkpointer": {
    "ttl": "7d"  // Auto-delete threads older than 7 days
  }
}
```

See [Configure TTL Guide](https://docs.langchain.com/langsmith/configure-ttl) for details.

### Managing Cron Jobs

**List All Cron Jobs**:

```python
cron_jobs = await client.crons.list()
for cron in cron_jobs:
    print(f"{cron['cron_id']}: {cron['schedule']} - {cron['assistant_id']}")
```

**Get Specific Cron Job**:

```python
cron = await client.crons.get("<CRON_ID>")
print(cron)
```

**Delete Cron Job**:

```python
await client.crons.delete("<CRON_ID>")
```

**CRITICAL**: Always delete cron jobs when no longer needed to avoid unwanted LLM API charges!

### Best Practices

#### 1. Defensive Deletion

```python
# Always clean up in finally block
cron_job = None
try:
    cron_job = await client.crons.create(...)
    # Use cron job...
except Exception as e:
    print(f"Error: {e}")
finally:
    if cron_job:
        await client.crons.delete(cron_job["cron_id"])
```

#### 2. Use Metadata for Tracking

```python
cron_job = await client.crons.create(
    "agent",
    schedule="0 9 * * *",
    input={...},
    metadata={
        "purpose": "daily_summary",
        "created_by": "user@example.com",
        "environment": "production"
    }
)
```

#### 3. Test Schedule First

```python
# Test with frequent schedule first
test_cron = await client.crons.create(
    "agent",
    schedule="*/5 * * * *",  # Every 5 minutes for testing
    input={...}
)

# After validation, update to production schedule
# (Delete test_cron, create production cron)
```

#### 4. Monitor Execution

```python
# Track cron job execution
runs = await client.runs.search(
    metadata={"cron_id": cron_job["cron_id"]}
)

for run in runs:
    if run["status"] == "error":
        print(f"Failed run: {run['run_id']} - {run.get('error')}")
```

---

## Webhooks

### Concept

Webhooks enable event-driven communication from LangGraph Platform to external services. When a run completes, Platform sends a POST request to your specified endpoint.

**Use Cases**:
- Notify external systems of completion
- Trigger downstream workflows
- Log results to external databases
- Send alerts or notifications
- Chain multiple services

### Supported Endpoints

Webhooks supported on these API endpoints:

| Operation | HTTP Method | Endpoint |
|-----------|-------------|----------|
| Create Run | `POST` | `/thread/{thread_id}/runs` |
| Create Thread Cron | `POST` | `/thread/{thread_id}/runs/crons` |
| Stream Run | `POST` | `/thread/{thread_id}/runs/stream` |
| Wait Run | `POST` | `/thread/{thread_id}/runs/wait` |
| Create Cron | `POST` | `/runs/crons` |
| Stream Run Stateless | `POST` | `/runs/stream` |
| Wait Run Stateless | `POST` | `/runs/wait` |

### Using Webhooks

**Basic Usage**:

```python
from langgraph_sdk import get_client

client = get_client(url="<DEPLOYMENT_URL>")
thread = await client.threads.create()

input_data = {"messages": [{"role": "user", "content": "Hello!"}]}

# Add webhook parameter
async for chunk in client.runs.stream(
    thread_id=thread["thread_id"],
    assistant_id="agent",
    input=input_data,
    stream_mode="events",
    webhook="https://my-server.app/my-webhook-endpoint"
):
    # Handle stream
    pass

# When run completes → POST request sent to webhook URL
```

**With Cron Jobs**:

```python
# Webhook triggered after each cron execution
cron_job = await client.crons.create(
    "agent",
    schedule="0 9 * * *",
    input={"messages": [{"role": "user", "content": "Daily report"}]},
    webhook="https://my-server.app/daily-report-complete"
)
```

### Webhook Payload

**Format**: Run object (same as API responses)

**Sample Payload**:

```json
{
  "run_id": "1ef6746e-5893-67b1-978a-0f1cd4060e16",
  "thread_id": "9dde5490-2b67-47c8-aa14-4bfec88af217",
  "assistant_id": "agent",
  "status": "success",
  "created_at": "2024-08-30T23:07:38.242730+00:00",
  "kwargs": {
    "input": {"messages": [{"role": "user", "content": "Hello!"}]},
    "config": {...},
    "metadata": {...}
  },
  "output": {
    "messages": [
      {"role": "user", "content": "Hello!"},
      {"role": "assistant", "content": "Hi there!"}
    ]
  }
}
```

### Webhook Security

#### Pattern 1: Query Parameter Token

```python
# Add secret token to webhook URL
webhook_url = "https://my-server.app/webhook?token=YOUR_SECRET_TOKEN"

async for chunk in client.runs.stream(
    thread_id=thread["thread_id"],
    assistant_id="agent",
    input=input_data,
    webhook=webhook_url
):
    pass
```

**Endpoint Implementation**:

```python
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()
WEBHOOK_SECRET = "YOUR_SECRET_TOKEN"

@app.post("/webhook")
async def webhook_handler(request: Request):
    # Validate token
    token = request.query_params.get("token")
    if token != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Process payload
    payload = await request.json()
    print(f"Run {payload['run_id']} completed with status: {payload['status']}")

    return {"status": "received"}
```

#### Pattern 2: Static Headers (langgraph.json)

**Available in langgraph-api ≥0.5.36**

```json
{
  "webhooks": {
    "headers": {
      "X-Custom-Header": "my-value",
      "X-Environment": "production"
    }
  }
}
```

**With Environment Variables**:

```json
{
  "webhooks": {
    "headers": {
      "Authorization": "Bearer ${{ env.LG_WEBHOOK_TOKEN }}"
    }
  }
}
```

**Custom Prefix**:

```json
{
  "webhooks": {
    "env_prefix": "MY_APP_",
    "headers": {
      "Authorization": "Bearer ${{ env.MY_APP_SECRET }}"
    }
  }
}
```

**Security Notes**:
- Only env vars with specified prefix accessible (default: `LG_WEBHOOK_`)
- Missing required env vars block server startup

#### Pattern 3: HMAC Signature (Custom Implementation)

```python
import hmac
import hashlib

SECRET_KEY = "your-secret-key"

# Sender (not built into Platform, requires middleware)
def create_signature(payload: str) -> str:
    return hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

# Receiver
@app.post("/webhook")
async def webhook_handler(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-Webhook-Signature")

    expected = hmac.new(
        SECRET_KEY.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process payload...
```

### Webhook URL Restrictions

**Available in langgraph-api ≥0.5.36**

**Configure in langgraph.json**:

```json
{
  "webhooks": {
    "url": {
      "allowed_domains": ["*.mycompany.com", "api.trusted-service.com"],
      "require_https": true,
      "allowed_ports": [443, 8443],
      "disable_loopback": true,
      "max_url_length": 2048
    }
  }
}
```

**Options**:

| Option | Description | Example |
|--------|-------------|---------|
| `allowed_domains` | Hostname allowlist (supports wildcards) | `["*.mycompany.com"]` |
| `require_https` | Reject `http://` URLs | `true` |
| `allowed_ports` | Explicit port allowlist | `[443, 8443]` |
| `disable_loopback` | Disallow internal calls | `true` |
| `max_url_length` | Max URL length | `2048` |

### Disable Webhooks

**Available in langgraph-api ≥0.2.78**

**Configure in langgraph.json**:

```json
{
  "http": {
    "disable_webhooks": true
  }
}
```

**When to disable**:
- Self-hosted deployments without network controls
- Simplify security posture
- Prevent untrusted payloads to internal endpoints

### Testing Webhooks

**Online Tools**:
- **[Beeceptor](https://beeceptor.com/)**: Create test endpoint, inspect payloads
- **[Webhook.site](https://webhook.site/)**: View/debug incoming requests in real-time

**Example with Webhook.site**:

```python
# Get temporary URL from https://webhook.site
test_url = "https://webhook.site/abc123def"

# Test webhook
async for chunk in client.runs.stream(
    thread_id=thread["thread_id"],
    assistant_id="agent",
    input={"messages": [{"role": "user", "content": "Test"}]},
    webhook=test_url
):
    pass

# View payload on webhook.site dashboard
```

---

## Common Patterns

### Pattern 1: Daily Report with Webhook Notification

```python
# Cron job generates report, webhook notifies completion
cron_job = await client.crons.create(
    "report_generator",
    schedule="0 9 * * *",  # 9 AM daily
    input={"messages": [{"role": "user", "content": "Generate daily sales report"}]},
    webhook="https://notifications.mycompany.com/report-complete",
    on_run_completed="keep"  # Keep for later retrieval
)

# Webhook endpoint sends email notification
@app.post("/report-complete")
async def report_complete_handler(run_data: dict):
    report = run_data["output"]["messages"][-1]["content"]
    send_email(to="team@company.com", subject="Daily Sales Report", body=report)
    return {"status": "ok"}
```

### Pattern 2: Chained Workflows

```python
# Graph 1 completes → Webhook triggers Graph 2
@app.post("/trigger-analysis")
async def trigger_analysis_handler(run_data: dict):
    # Extract output from first graph
    summary = run_data["output"]["summary"]

    # Trigger second graph
    thread = await client.threads.create()
    await client.runs.create(
        thread_id=thread["thread_id"],
        assistant_id="analyst",
        input={"summary": summary}
    )
```

### Pattern 3: Error Alerting

```python
# Webhook monitors for errors
@app.post("/monitor-runs")
async def monitor_runs_handler(run_data: dict):
    if run_data["status"] == "error":
        # Alert on-call engineer
        send_alert(
            severity="high",
            message=f"Run {run_data['run_id']} failed: {run_data.get('error')}"
        )

# Use with all runs
async for chunk in client.runs.stream(
    thread_id=thread["thread_id"],
    assistant_id="agent",
    input=input_data,
    webhook="https://monitoring.mycompany.com/monitor-runs"
):
    pass
```

---

## Production Checklist

**Cron Jobs**:
- [ ] **Deletion Strategy**: Always delete unused cron jobs
- [ ] **TTL Configuration**: Set `checkpointer.ttl` if using `on_run_completed="keep"`
- [ ] **Monitoring**: Track cron execution success/failure
- [ ] **Schedule Validation**: Test schedule before production deployment
- [ ] **Metadata**: Add descriptive metadata for tracking

**Webhooks**:
- [ ] **Security**: Implement authentication (token, headers, HMAC)
- [ ] **URL Restrictions**: Configure `allowed_domains` and `require_https`
- [ ] **Error Handling**: Handle webhook endpoint failures gracefully
- [ ] **Testing**: Validate webhooks with test tools before production
- [ ] **Logging**: Log incoming webhooks for debugging

---

## References

- [Cron Jobs Documentation](https://docs.langchain.com/langsmith/cron-jobs)
- [Webhooks Documentation](https://docs.langchain.com/langgraph-platform/use-webhooks)
- [Configure TTL Guide](https://docs.langchain.com/langsmith/configure-ttl)
- [LangGraph Server API Reference](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref.html)
- [Crontab Guru](https://crontab.cronhub.io/) - Interactive cron expression builder

---

**Created**: 2026-01-14
**LangGraph Platform Version**: Latest
**Status**: Active
