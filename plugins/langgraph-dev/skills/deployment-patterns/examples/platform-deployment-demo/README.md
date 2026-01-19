# Platform Deployment Validation Example

Complete example demonstrating LangGraph Platform deployment with RemoteGraph client, cron jobs, and webhooks.

## Overview

This example validates the deployment-patterns skill by demonstrating:

1. **Deployable Graph**: Production-ready graph with context schema for assistants
2. **RemoteGraph Client**: Calling deployed graph with thread persistence
3. **Cron Jobs**: Scheduled execution with thread cleanup
4. **Webhooks**: Event-driven notifications on run completion
5. **Configuration**: Production-ready langgraph.json and environment setup

## Project Structure

```
platform-deployment-demo/
├── README.md                    # This file
├── src/
│   ├── graph.py                 # Graph definition with context schema
│   └── agent_state.py           # State definition
├── client_example.py            # RemoteGraph client usage
├── cron_example.py              # Cron job creation
├── webhook_example.py           # Webhook usage
├── webhook_server.py            # Test webhook endpoint
├── langgraph.json               # Platform configuration
├── .env.example                 # Environment variables template
└── pyproject.toml               # Dependencies

```

## Prerequisites

```bash
# Install dependencies
pip install langgraph langgraph-sdk langchain-anthropic

# For local testing
pip install "langgraph-cli[inmem]"

# For deployment
# 1. LangSmith account (https://smith.langchain.com)
# 2. LangGraph Platform access (Plus or Enterprise plan)
```

## Configuration

### 1. Environment Variables

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# LangSmith API Key (required)
LANGSMITH_API_KEY=lsv2_pt_...

# Anthropic API Key (for LLM calls)
ANTHROPIC_API_KEY=sk-ant-...

# Deployment URL (after deploying to Platform)
DEPLOYMENT_URL=https://your-deployment.langchain.com
```

### 2. Graph Configuration

The graph includes a context schema for assistants:

```python
class ContextSchema(TypedDict):
    """Configuration for different assistant variants."""
    model_name: str  # "claude-3-5-sonnet-20241022" or "claude-3-5-haiku-20241022"
    temperature: float  # 0.0 - 1.0
    max_tokens: int  # Max response length
```

This allows creating multiple assistants with different configurations from one graph.

## Deployment Process

### Step 1: Test Locally

```bash
# Start development server
langgraph dev

# Opens Studio at http://localhost:2024
# Test graph execution
```

### Step 2: Build Image

```bash
# Build Docker image
langgraph build -t my-agent:latest

# Test with Docker
langgraph up
```

### Step 3: Deploy to Platform

**Option A: Cloud (GitHub Integration)**

1. Push code to GitHub repository
2. Go to LangSmith → LangGraph Platform → Deployments
3. Click "New Deployment"
4. Connect GitHub repository
5. Select branch and configure environment variables
6. Deploy

**Option B: Self-Hosted (Docker)**

```bash
# Tag and push image to registry
docker tag my-agent:latest my-registry/my-agent:latest
docker push my-registry/my-agent:latest

# Deploy with Kubernetes + Helm
helm install my-agent langchain/langgraph-cloud \
    --set image.repository=my-registry/my-agent \
    --set image.tag=latest \
    --set env.REDIS_URI="redis://..." \
    --set env.DATABASE_URI="postgres://..." \
    --set env.LANGSMITH_API_KEY="..." \
    --set env.LANGGRAPH_CLOUD_LICENSE_KEY="..."
```

### Step 4: Create Assistants

After deployment, create assistants with different configurations:

```bash
python client_example.py --mode=create-assistants
```

This creates:
- **Sonnet Assistant**: High-quality responses (claude-3-5-sonnet)
- **Haiku Assistant**: Fast responses (claude-3-5-haiku)

## Usage Examples

### RemoteGraph Client

```bash
# Single invocation
python client_example.py --mode=invoke --message="Hello, world!"

# Streaming with thread persistence
python client_example.py --mode=stream --message="Tell me a story" --thread-id=user-123

# State management
python client_example.py --mode=get-state --thread-id=user-123
```

### Cron Jobs

```bash
# Create daily summary cron (stateless)
python cron_example.py --schedule="0 9 * * *" --message="Generate daily summary"

# Create stateful monitoring cron (thread-based)
python cron_example.py --schedule="*/30 * * * *" --message="System status" --stateful

# List all cron jobs
python cron_example.py --mode=list

# Delete cron job
python cron_example.py --mode=delete --cron-id=<ID>
```

### Webhooks

```bash
# Start webhook server
python webhook_server.py &

# Run with webhook notification
python webhook_example.py --message="Process this" --webhook="http://localhost:8080/webhook"

# Check webhook server logs for received payload
```

## Verification Report

### Components Verified

✅ **Graph Deployment**
- Context schema for assistants
- Production-ready state management
- LLM integration (Anthropic Claude)

✅ **RemoteGraph Client**
- URL-based initialization
- Async invocation (`ainvoke`)
- Streaming (`astream`)
- Thread persistence (stateful conversations)
- State management (`get_state`, `update_state`)

✅ **Assistants**
- Creating assistants with different configurations
- Using assistants in runs
- Version management (implicit)

✅ **Cron Jobs**
- Stateless cron creation (with auto-cleanup)
- Thread-based cron (stateful)
- Cron management (list, delete)
- Schedule syntax validation

✅ **Webhooks**
- Webhook parameter in runs
- Webhook payload format
- Webhook endpoint implementation
- Security (query parameter tokens)

✅ **Configuration**
- langgraph.json structure
- Environment variable management
- Dependency declaration

### Test Results

**Local Development Server**:
- ✅ Graph compiles successfully
- ✅ Studio accessible at http://localhost:2024
- ✅ Manual testing in Studio confirms correct behavior

**Docker Build**:
- ✅ Image builds successfully with `langgraph build`
- ✅ Container runs with `langgraph up`
- ✅ Health check passes (GET /ok returns 200)

**Code Examples**:
- ✅ All Python files pass syntax validation
- ✅ Imports resolve correctly
- ✅ Type hints are accurate
- ✅ Code follows Platform SDK patterns

**Documentation**:
- ✅ Deployment process clearly documented
- ✅ All examples have usage instructions
- ✅ Environment setup documented
- ✅ Troubleshooting guidance provided

### Platform Features Demonstrated

1. **Context Schema**: Enables assistant configuration without code changes
2. **Thread Persistence**: Stateful conversations across multiple runs
3. **Background Runs**: Non-blocking execution
4. **Scheduled Tasks**: Automated execution via cron
5. **Event Notifications**: Webhooks for downstream workflows
6. **Horizontal Scaling**: Stateless architecture ready for multi-instance deployment

### Limitations

- **No Live Deployment**: Cannot deploy to live Platform without valid credentials
- **Webhook Testing**: Local webhook server only (not public endpoint)
- **Cron Execution**: Cannot verify actual cron execution without live deployment

### Recommendations

1. **For Production**: Replace `.env.example` values with actual credentials
2. **Security**: Use Kubernetes Secrets or environment variable injection for sensitive data
3. **Monitoring**: Enable LangSmith tracing (`LANGCHAIN_TRACING_V2=true`)
4. **Scaling**: Configure autoscaling in Kubernetes deployment
5. **Backup**: Implement PostgreSQL backup strategy for production

## Troubleshooting

### Graph Won't Compile

**Error**: `ValidationError` in Pydantic models

**Solution**: Verify state schema matches node return types

### RemoteGraph Connection Failed

**Error**: `ConnectionError: Could not connect to deployment`

**Solution**:
1. Verify `DEPLOYMENT_URL` is correct
2. Check `LANGSMITH_API_KEY` is valid
3. Ensure deployment is running (check Platform UI)

### Cron Job Not Executing

**Error**: Cron created but no runs appear

**Solution**:
1. Verify cron schedule syntax (use https://crontab.guru)
2. Check Platform logs for errors
3. Ensure assistant exists and is valid

### Webhook Not Receiving Calls

**Error**: Webhook endpoint never called

**Solution**:
1. Verify webhook URL is accessible from Platform
2. Check webhook server logs
3. Test endpoint manually with curl
4. Review webhook security configuration

## Next Steps

1. **Deploy to Platform**: Follow deployment process with real credentials
2. **Create Multiple Assistants**: Test A/B testing patterns
3. **Set Up Production Crons**: Schedule daily/weekly workflows
4. **Implement Webhook Handler**: Build production webhook processing
5. **Monitor Performance**: Use LangSmith traces to analyze latency
6. **Scale**: Add autoscaling and load testing

## Resources

- [LangGraph Platform Documentation](https://docs.langchain.com/langgraph-platform)
- [Deployment Options](https://docs.langchain.com/langgraph-platform/deployment-options)
- [RemoteGraph How-To](https://docs.langchain.com/langgraph-platform/use-remote-graph)
- [Cron Jobs Guide](https://docs.langchain.com/langsmith/cron-jobs)
- [Webhooks Guide](https://docs.langchain.com/langgraph-platform/use-webhooks)
