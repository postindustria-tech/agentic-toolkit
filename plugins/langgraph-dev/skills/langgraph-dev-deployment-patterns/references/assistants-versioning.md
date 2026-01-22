# Assistants and Versioning

Comprehensive guide to creating, configuring, and managing assistants on LangGraph Platform.

## Overview

**Assistants** are instances of a graph with specific configurations, allowing you to create multiple specialized versions of the same graph architecture optimized for different use cases through configuration variations rather than structural changes.

**Key Concept**: Same graph logic, different configurations (prompts, models, tools, parameters)

**Example**: Writing agent with one graph, multiple assistants:
- **Blog Assistant**: Uses GPT-4, formal tone, long-form prompts
- **Tweet Assistant**: Uses GPT-3.5, casual tone, concise prompts
- **Email Assistant**: Uses Claude, professional tone, structured prompts

**Platform-Only**: Assistants are a LangGraph Platform feature, not available in open-source LangGraph.

## Configuration Foundation

### Context Schema (Open Source)

Assistants build on LangGraph's open-source configuration concept:

```python
from langgraph.graph import StateGraph
from typing import TypedDict
from langgraph.types import Runtime

# Define context schema
class ContextSchema(TypedDict):
    model_name: str
    system_prompt: str
    temperature: float

# Use context in nodes
def call_model(state: AgentState, runtime: Runtime[ContextSchema]):
    # Access configuration
    model = runtime.context.get("model_name", "anthropic")
    system_prompt = runtime.context.get("system_prompt", "You are helpful")
    temperature = runtime.context.get("temperature", 0.7)

    # Use configuration
    llm = get_llm(model, temperature=temperature)
    response = llm.invoke([
        {"role": "system", "content": system_prompt},
        *state["messages"]
    ])

    return {"messages": [response]}

# Compile with context schema
builder = StateGraph(AgentState, context_schema=ContextSchema)
builder.add_node("call_model", call_model)
graph = builder.compile()
```

**How it works**:
1. Define `context_schema` with configurable fields
2. Access context via `runtime.context` in nodes
3. Deploy graph → Platform auto-creates default assistant
4. Create additional assistants with different contexts

## Assistant Management

### Creating Assistants

**SDK Method**:

```python
from langgraph_sdk import get_client

client = get_client(url="<DEPLOYMENT_URL>")

# Create assistant with specific configuration
assistant = await client.assistants.create(
    "agent",  # Graph name from langgraph.json
    context={
        "model_name": "openai",
        "system_prompt": "You are a helpful assistant",
        "temperature": 0.7
    },
    name="OpenAI Assistant",
    metadata={"team": "product", "version": "1.0"}
)

print(assistant)
# Output:
# {
#   "assistant_id": "62e209ca-9154-432a-b9e9-2d75c7a9219b",
#   "graph_id": "agent",
#   "name": "OpenAI Assistant",
#   "context": {"model_name": "openai", "system_prompt": "...", ...},
#   "metadata": {"team": "product", "version": "1.0"},
#   "created_at": "2024-08-31T03:09:10.230718+00:00",
#   "updated_at": "2024-08-31T03:09:10.230718+00:00"
# }
```

**UI Method** (LangGraph Platform):
1. Navigate to deployment → **Assistants** tab
2. Click **+ New assistant**
3. Fill form:
   - Graph selection
   - Name and description
   - Configuration (based on graph's context schema)
4. Click **Create assistant**
5. Opens in LangGraph Studio for testing

### Using Assistants

**With Runs**:

```python
# Create thread
thread = await client.threads.create()

# Run with specific assistant
input_data = {"messages": [{"role": "user", "content": "who made you?"}]}

async for event in client.runs.stream(
    thread["thread_id"],
    assistant["assistant_id"],  # Use specific assistant
    input=input_data,
    stream_mode="updates"
):
    print(event.data)

# Output uses assistant's configuration
# e.g., "I was created by OpenAI..." (because model_name="openai")
```

**In Studio**:
1. Deployment → **Assistants** tab
2. Select assistant → Click **Studio** button
3. Studio loads with selected assistant
4. Inputs use assistant's configuration

### Listing Assistants

```python
# Get all assistants for deployment
assistants = await client.assistants.list()

for asst in assistants:
    print(f"{asst['name']}: {asst['assistant_id']}")

# Get specific assistant
assistant = await client.assistants.get("<ASSISTANT_ID>")
```

## Versioning

### Creating New Versions

**SDK Method**:

```python
# Update assistant → Creates new version
updated_assistant = await client.assistants.update(
    assistant["assistant_id"],
    context={
        "model_name": "openai",  # Keep existing
        "system_prompt": "You are an unhelpful assistant!",  # Changed
        "temperature": 0.9  # Changed
    },
    name="OpenAI Assistant v2"  # Optional: update name
)

# New version automatically becomes active
print(updated_assistant["version"])  # 2
```

**CRITICAL**: Must pass **ENTIRE context** (and metadata if used). Update endpoint creates new versions from scratch, doesn't merge with previous versions.

**UI Method** (Platform):
1. Assistants tab → Click **Edit** for assistant
2. Modify configuration fields
3. Save → Creates new version, sets as active

**UI Method** (Studio):
1. **Manage Assistants** button
2. Select assistant → Edit configuration
3. Save → New version created

### Version Management

**List Versions**:

```python
versions = await client.assistants.get_versions("<ASSISTANT_ID>")

for v in versions:
    print(f"Version {v['version']}: {v['created_at']}")
    print(f"  Active: {v['is_active']}")
    print(f"  Context: {v['context']}")
```

**Rollback to Previous Version**:

```python
# Set version 1 as active
await client.assistants.set_latest("<ASSISTANT_ID>", version=1)

# Now all runs with this assistant ID use version 1 configuration
```

**UI Method** (Studio):
1. **Manage Assistants** button
2. Select assistant and version
3. Toggle **Active** switch
4. Selected version becomes active

**Delete Assistant**:

```python
# CAUTION: Deletes ALL versions
await client.assistants.delete("<ASSISTANT_ID>")
```

**WARNING**: Cannot delete individual versions, only entire assistant with all versions.

## Common Patterns

### Pattern 1: Multi-Model Strategy

```python
# Create assistants for different models
models = [
    ("gpt-4", "GPT-4 Assistant"),
    ("claude-3-opus", "Claude Opus Assistant"),
    ("gpt-3.5-turbo", "GPT-3.5 Assistant")
]

assistants = {}
for model, name in models:
    asst = await client.assistants.create(
        "agent",
        context={"model_name": model},
        name=name
    )
    assistants[model] = asst

# Use based on requirements
result = await client.runs.create(
    thread_id=thread["thread_id"],
    assistant_id=assistants["gpt-4"]["assistant_id"],  # Use GPT-4 for complex task
    input=input_data
)
```

### Pattern 2: Environment-Specific Assistants

```python
# Development assistant (verbose logging, lower temperature)
dev_assistant = await client.assistants.create(
    "agent",
    context={
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.3,
        "log_level": "DEBUG"
    },
    name="Development Assistant",
    metadata={"environment": "development"}
)

# Production assistant (production model, optimized temperature)
prod_assistant = await client.assistants.create(
    "agent",
    context={
        "model_name": "gpt-4",
        "temperature": 0.7,
        "log_level": "INFO"
    },
    name="Production Assistant",
    metadata={"environment": "production"}
)
```

### Pattern 3: A/B Testing

```python
# Control group
control = await client.assistants.create(
    "agent",
    context={"system_prompt": "You are a helpful assistant"},
    name="Control",
    metadata={"experiment": "prompt_test", "variant": "A"}
)

# Variant group
variant = await client.assistants.create(
    "agent",
    context={"system_prompt": "You are an expert assistant"},
    name="Variant",
    metadata={"experiment": "prompt_test", "variant": "B"}
)

# Randomly assign users
import random
user_assistant = random.choice([control, variant])

result = await client.runs.create(
    thread_id=thread["thread_id"],
    assistant_id=user_assistant["assistant_id"],
    input=input_data
)
```

### Pattern 4: Gradual Rollout

```python
# Version 1 (current production)
v1_assistant = await client.assistants.create(
    "agent",
    context={"system_prompt": "Old prompt", "model_name": "gpt-4"},
    name="V1 Assistant"
)

# Version 2 (new experimental)
v2_context = {
    "system_prompt": "Improved prompt",
    "model_name": "gpt-4-turbo"
}

# Create v2 as new assistant (not version of v1)
v2_assistant = await client.assistants.create(
    "agent",
    context=v2_context,
    name="V2 Assistant (Beta)"
)

# Gradual rollout: 10% to v2, 90% to v1
def get_assistant_for_user(user_id: str):
    if hash(user_id) % 10 == 0:  # 10% of users
        return v2_assistant["assistant_id"]
    return v1_assistant["assistant_id"]

# Once v2 validated, update v1 to v2's config
await client.assistants.update(
    v1_assistant["assistant_id"],
    context=v2_context
)
# Now 100% on v2 config, delete beta assistant
```

## Best Practices

### 1. Comprehensive Context Updates

```python
# ❌ Bad - Incomplete context
await client.assistants.update(
    assistant_id,
    context={"temperature": 0.9}  # Missing other fields!
)

# ✅ Good - Full context
current = await client.assistants.get(assistant_id)
await client.assistants.update(
    assistant_id,
    context={
        **current["context"],  # Keep existing
        "temperature": 0.9  # Update specific field
    }
)
```

### 2. Meaningful Names and Metadata

```python
# ✅ Good - Descriptive metadata
assistant = await client.assistants.create(
    "agent",
    context={...},
    name="Customer Support GPT-4 (Friendly Tone)",
    metadata={
        "use_case": "customer_support",
        "model": "gpt-4",
        "tone": "friendly",
        "department": "support",
        "created_by": "user@example.com",
        "version": "2.1"
    }
)
```

### 3. Default Assistant Pattern

```python
# Create a default assistant on deployment
default_assistant = await client.assistants.create(
    "agent",
    context={"model_name": "gpt-4", "temperature": 0.7},
    name="Default Assistant",
    metadata={"is_default": True}
)

# Use default when no specific assistant needed
def get_assistant(assistant_id=None):
    if assistant_id:
        return assistant_id

    # Get default
    assistants = await client.assistants.list()
    for asst in assistants:
        if asst["metadata"].get("is_default"):
            return asst["assistant_id"]

    raise ValueError("No default assistant found")
```

### 4. Version Naming Convention

```python
# Track versions in metadata
assistant = await client.assistants.create(
    "agent",
    context={...},
    name="Production Assistant",
    metadata={
        "version": "2.1.0",  # Semantic versioning
        "changelog": "Updated system prompt for clarity",
        "deployed_at": "2026-01-14T10:00:00Z"
    }
)
```

### 5. Safe Rollback Strategy

```python
# Before updating, note current version
current_version = await client.assistants.get(assistant_id)
print(f"Current version: {current_version['version']}")

# Update
await client.assistants.update(assistant_id, context=new_context)

# If issues, rollback
await client.assistants.set_latest(assistant_id, current_version['version'])
```

## Migration Strategies

### Strategy 1: Blue-Green Deployment

```python
# Create new "green" assistant
green = await client.assistants.create(
    "agent",
    context=new_config,
    name="Green Assistant"
)

# Test thoroughly in green
# ...

# Switch traffic from blue to green
# (Update application to use green assistant_id)

# Keep blue for rollback if needed
```

### Strategy 2: Canary Deployment

```python
# Create canary assistant
canary = await client.assistants.create(
    "agent",
    context=new_config,
    name="Canary Assistant",
    metadata={"is_canary": True, "rollout_percentage": 5}
)

# Route 5% of traffic to canary
def get_assistant_for_request(request_id):
    if hash(request_id) % 100 < 5:  # 5% canary
        return canary["assistant_id"]
    return production["assistant_id"]

# Monitor metrics
# If canary healthy, increase rollout_percentage
# Eventually update production assistant to canary config
```

## Troubleshooting

### Issue: Assistant Not Using Latest Version

**Symptom**: Updated assistant but runs still use old configuration

**Solutions**:
1. Verify update succeeded: `await client.assistants.get(assistant_id)`
2. Check version is active: Look for `"is_active": true` in version
3. Clear any client-side caching
4. Verify assistant_id is correct in run creation

### Issue: Missing Context Fields

**Symptom**: `KeyError` in node accessing context

**Solutions**:
1. Verify context_schema matches assistant context
2. Use `.get()` with defaults: `runtime.context.get("field", default)`
3. Check assistant context includes all required fields

### Issue: Cannot Delete Version

**Symptom**: Want to delete single version, only sees delete assistant

**Solution**: Cannot delete individual versions. Instead:
1. Set active version to desired version
2. Ignore unwanted versions (they won't be used)
3. Or create new assistant with desired config

### Issue: Assistants Not Showing in UI

**Symptom**: Created assistants not visible in Platform UI

**Solutions**:
1. Refresh page
2. Verify deployment is correct
3. Check graph_id matches deployed graph name
4. Verify API key has correct permissions

## Production Checklist

- [ ] **Default Assistant**: Created and marked in metadata
- [ ] **Naming Convention**: Descriptive names + metadata
- [ ] **Version Tracking**: Use metadata for version history
- [ ] **Rollback Plan**: Know how to use `set_latest()`
- [ ] **Testing**: Test new assistants before production use
- [ ] **Monitoring**: Track which assistants used in production
- [ ] **Documentation**: Document assistant purposes and configurations
- [ ] **Cleanup**: Delete unused assistants to reduce clutter

## References

- [Assistants Overview](https://docs.langchain.com/langgraph-platform/assistants)
- [Manage Assistants How-To](https://docs.langchain.com/langgraph-platform/configuration-cloud)
- [Python SDK AssistantsClient Reference](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/#assistantsclient)
- [LangGraph Configuration Concept](https://langchain-ai.github.io/oss/python/langgraph/graph-api#runtime-context)
- [Platform API Reference](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref/#tag/assistants)

---

**Created**: 2026-01-14
**LangGraph Platform Version**: Latest
**Status**: Active
