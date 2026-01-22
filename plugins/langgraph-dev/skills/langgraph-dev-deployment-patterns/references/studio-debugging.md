# LangGraph Studio Debugging Workflows

Comprehensive guide to debugging deployed and local LangGraph applications using LangGraph Studio.

## Overview

LangGraph Studio is a specialized agent IDE that enables visualization, interaction, and debugging of agentic systems implementing the LangGraph Server API protocol. Studio integrates with LangSmith for tracing, evaluation, and prompt engineering.

**Key Capabilities**:
- Visualize graph architecture
- Run and interact with agents
- Manage assistants and threads
- Iterate on prompts
- Run experiments over datasets
- Manage long-term memory
- Debug agent state via time travel
- Inspect traces and states

## Studio Modes

### Graph Mode

**When to use**: Maximum visibility into agent execution, debugging, and development

**Features**:
- Full execution details (nodes traversed, intermediate states)
- LangSmith integrations (datasets, playground)
- State inspection at every checkpoint
- Time travel and forking
- Breakpoints and debugging

### Chat Mode

**When to use**: Testing chat agents, business user demos, behavior validation

**Requirements**: Graph state must include or extend `MessagesState`

**Features**:
- Simplified chat interface
- Message editing and regeneration
- Thread history
- Less technical detail (focused on behavior)

## Access Patterns

### Pattern 1: Deployed Graphs (LangGraph Platform)

**Access Studio from LangSmith UI**:

1. Navigate to **LangGraph Platform Deployments** tab in LangSmith
2. Select your deployment
3. Click **LangGraph Studio** button
4. Studio loads connected to live deployment

**Capabilities**:
- Create, read, update threads
- Manage assistants
- Inspect production conversations
- Debug issues from production traces

**Use cases**:
- Production debugging
- Assistant configuration testing
- Thread inspection
- Memory management

### Pattern 2: Local Development Server

**Setup**:

```bash
# Install LangGraph CLI
pip install -U "langgraph-cli[inmem]"

# OR with UV
uv add "langgraph-cli[inmem]"

# Start development server
langgraph dev

# With secure tunnel (for Safari compatibility)
langgraph dev --tunnel
```

**Output**:
```
> Ready!
> - API: http://localhost:2024
> - Docs: http://localhost:2024/docs
> - LangGraph Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

**Access Studio**:
- **Auto-redirect**: Automatically opens Studio on first run
- **Direct URL**: Navigate to `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`
- **LangSmith UI**: Click **LangGraph Studio** → Enter `http://127.0.0.1:2024` → **Connect**

**Features**:
- Watch mode (auto-reload on code changes)
- In-memory persistence
- Local-only (no data sent to cloud if `LANGSMITH_TRACING=false`)

### Pattern 3: Local Development with Debugger

**Setup with debugpy**:

```bash
# Install debugger
pip install debugpy

# Start server with debug port
langgraph dev --debug-port 5678
```

**VS Code Configuration** (`launch.json`):

```json
{
    "name": "Attach to LangGraph",
    "type": "debugpy",
    "request": "attach",
    "connect": {
        "host": "0.0.0.0",
        "port": 5678
    }
}
```

**Debugging workflow**:
1. Start server with `--debug-port`
2. Set breakpoints in VS Code
3. Attach debugger
4. Trigger graph execution from Studio
5. Step through code with full variable inspection

## Thread Management

### Viewing Threads

**Graph Mode**:
1. Top-right dropdown: Select existing thread or **+ New Thread**
2. Thread history populates in right pane
3. Adjust detail level with slider (granularity control)
4. Collapse/expand individual turns, nodes, state keys
5. Switch between **Pretty** and **JSON** views

**Chat Mode**:
1. Right pane: View all threads
2. Select thread → History populates in center panel
3. Plus button: Create new thread

### Editing Thread History

**Graph Mode - Edit State**:

```
1. Select node in thread history
2. Click "Edit node state"
3. Modify state JSON
4. Click "Fork" to create new forked run from that checkpoint
```

**Alternative: Re-run without editing**:
```
1. Select checkpoint
2. Click "Re-run from here"
3. Creates new fork without state changes
4. Useful for testing assistant/configuration changes
```

**Chat Mode**:
- **Edit human message**: Click edit button → Modify → Submit (creates fork)
- **Regenerate AI message**: Click retry icon (re-generates from that point)

## Time Travel Debugging

**Concept**: Replay and fork agent actions to understand reasoning, debug mistakes, explore alternatives

### Use Cases

1. **Bug Investigation**: Replay exact execution that led to error
2. **What-if Analysis**: Fork from checkpoint and try different inputs/state
3. **Behavior Understanding**: Step through reasoning process
4. **Alternative Exploration**: Test different paths from same starting point

### Workflow

```
1. Identify checkpoint to investigate
2. Inspect state at that checkpoint
3. Option A: Re-run from checkpoint (same state)
4. Option B: Edit state and fork (modified execution)
5. Compare original vs forked execution
6. Iterate until issue understood/resolved
```

**Example**:
```
Original execution:
  START → classify_intent → retrieve_docs → [ERROR]

Time travel:
  1. Inspect state at classify_intent checkpoint
  2. Notice intent="query" but should be "search"
  3. Edit state: intent="search"
  4. Fork from classify_intent
  5. New execution: classify_intent → search_docs → generate_response → SUCCESS
```

## State Inspection

### Granularity Control

**Slider** (Graph Mode):
- **Left**: Less detail (high-level state)
- **Right**: More detail (full state dump)

**Collapsible Sections**:
- **Turns**: Individual conversation turns
- **Nodes**: Node-level outputs
- **State Keys**: Individual state fields

### Pretty vs JSON Views

**Pretty View**:
- Human-readable formatting
- Nested structures expanded
- Good for quick inspection

**JSON View**:
- Raw JSON format
- Copy-paste for analysis
- Machine-readable

## Interactive Debugging Features

### Static Breakpoints

**Purpose**: Pause execution at specific nodes for human intervention

**Setup in Graph**:
```python
# In graph definition
graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review"]  # Pauses before this node
)
```

**Studio Workflow**:
1. Run graph in Studio
2. Execution pauses at breakpoint
3. Inspect state
4. Option A: Continue execution
5. Option B: Edit state and continue
6. Option C: Cancel execution

**Use cases**:
- Human-in-the-loop approval
- State validation before expensive operations
- Manual intervention points

### Prompt Iteration

**Workflow**:
1. Run graph in Studio
2. Identify node with prompt to improve
3. Use Studio to edit prompt inline
4. Re-run from that checkpoint
5. Compare outputs
6. Iterate until satisfied

**LangSmith Integration**:
- Edit prompts in LangSmith Playground
- Test variations
- Deploy improved prompts

## Dataset and Experimentation

### Add to Dataset

**Purpose**: Capture interesting examples for evaluation/testing

**Workflow**:
1. Run graph in Studio
2. Identify good/bad example
3. Click "Add to dataset"
4. Select dataset or create new
5. Example saved with full context

**Use cases**:
- Building test suites
- Regression testing
- Evaluation benchmarks

### Run Experiments

**Purpose**: Test graph behavior across multiple examples

**Workflow**:
1. Create dataset (or use existing)
2. In Studio: Select "Run experiments"
3. Choose dataset
4. Select assistant/configuration
5. Run batch evaluation
6. Analyze results

**Metrics tracked**:
- Success rate
- Latency per run
- Error types
- State evolution

## Memory Management

**Studio provides UI for managing long-term memory** (Store interface):

- **View namespaces**: Inspect memory organization
- **Search memories**: Query stored facts
- **Edit entries**: Update or delete memories
- **Add memories**: Manually seed knowledge

**Use cases**:
- Debugging memory retrieval issues
- Seeding test data
- Inspecting cross-conversation knowledge
- Cleaning up stale memories

## Trace Debugging

### Clone Traces

**Purpose**: Import production traces into Studio for debugging

**Workflow**:
1. Find problematic trace in LangSmith
2. In Studio: "Clone trace"
3. Paste trace ID
4. Studio recreates execution
5. Debug with time travel and state inspection

**Use cases**:
- Production issue investigation
- Reproducing user-reported bugs
- Understanding edge cases

### Trace Visualization

**Features**:
- Execution timeline
- Node call hierarchy
- LLM token usage
- Latency breakdown
- Error stack traces

## Best Practices

### 1. Local Development Workflow

```bash
# Development loop
1. langgraph dev  # Start server with watch mode
2. Make code changes → Auto-reload
3. Test in Studio → Inspect results
4. Iterate until satisfied
5. Deploy to Platform
6. Debug production issues with Studio → Platform
```

### 2. Disable Tracing for Privacy

```python
# In .env file
LANGSMITH_TRACING=false  # No data sent to cloud
```

**When to disable**:
- Sensitive data
- Local-only development
- Privacy requirements

### 3. Use Graph Mode for Debugging

**Graph Mode** for development and debugging (detailed state)
**Chat Mode** for behavior testing and demos (simplified view)

### 4. Leverage Time Travel

```
# Don't just re-run from start
❌ Bad: Run → Error → Fix → Run entire graph again

# Use time travel to iterate faster
✅ Good: Run → Error → Edit state at error node → Fork → Test fix
```

### 5. Build Test Datasets

```
# As you debug, capture examples
1. Find interesting case in Studio
2. Add to dataset
3. Use for regression testing
4. Prevents future regressions
```

### 6. Combine Studio + Debugger

**For complex bugs**:
```
1. Studio: Identify problematic node
2. Set breakpoint in code at that node
3. Debugger: Stepthrough execution
4. Inspect variables, stack trace
5. Fix → Test in Studio → Verify
```

## Troubleshooting

### Safari Localhost Issue

**Problem**: Safari blocks `localhost` connections

**Solution**:
```bash
langgraph dev --tunnel  # Creates secure tunnel
```

### Studio Not Connecting

**Symptoms**: "Could not connect to server" error

**Solutions**:
1. Verify server running: `http://localhost:2024/docs`
2. Check firewall settings
3. Ensure correct `baseUrl` in Studio
4. Try `--host 0.0.0.0` flag

### Watch Mode Not Reloading

**Symptoms**: Code changes not reflected

**Solutions**:
1. Check file is in watched directories
2. Verify syntax errors (check terminal)
3. Restart `langgraph dev`
4. Check `.dockerignore` / `.gitignore` not blocking files

### Debugger Won't Attach

**Symptoms**: VS Code can't connect to debugpy

**Solutions**:
1. Verify debug port correct (default: 5678)
2. Check firewall allows connections
3. Ensure debugpy installed
4. Try `"host": "localhost"` instead of `"0.0.0.0"`

## Production Debugging Workflow

```
1. User reports issue
   ↓
2. Find trace in LangSmith
   ↓
3. Open deployment in Studio (Platform)
   ↓
4. Clone trace into Studio
   ↓
5. Use time travel to inspect states
   ↓
6. Identify root cause
   ↓
7. Reproduce locally with langgraph dev
   ↓
8. Fix → Test in local Studio
   ↓
9. Deploy fix → Verify in production Studio
```

## Comparison: Studio vs Local Debugging

| Feature | Studio | Local Debugger |
|---------|--------|----------------|
| State inspection | ✅ Full state at checkpoints | ✅ Real-time variables |
| Time travel | ✅ Fork and replay | ❌ Not available |
| Breakpoints | ⚠️ Static (predefined) | ✅ Dynamic (any line) |
| Thread management | ✅ Full UI | ❌ Manual |
| Production access | ✅ Direct connection | ❌ Requires reproduction |
| Code stepping | ❌ Not available | ✅ Line-by-line |
| Visualization | ✅ Graph + state UI | ❌ Text-only |

**Recommendation**: Use both - Studio for graph-level debugging, local debugger for code-level issues

## Integration with LangSmith

### Tracing

**Auto-enabled** when `LANGSMITH_TRACING=true`:
- Every Studio run traced to LangSmith
- Execution timeline
- Token usage
- Latency metrics
- Error tracking

### Datasets

**Bi-directional integration**:
- Add examples from Studio → LangSmith datasets
- Run experiments on LangSmith datasets from Studio

### Playground

**Prompt engineering workflow**:
- Test prompts in LangSmith Playground
- Deploy to graph
- Validate in Studio
- Iterate

## References

- [LangGraph Studio Overview](https://docs.langchain.com/langgraph-platform/langgraph-studio)
- [Quick Start Guide](https://docs.langchain.com/langgraph-platform/quick-start-studio)
- [Manage Threads](https://docs.langchain.com/langgraph-platform/threads-studio)
- [Time Travel Concept](https://langchain-ai.github.io/langgraph/concepts/tracing/)
- [Troubleshooting Studio](https://langchain-ai.github.io/langgraph-platform/troubleshooting-studio)

---

**Created**: 2026-01-14
**LangGraph CLI Version**: Latest
**Status**: Active
