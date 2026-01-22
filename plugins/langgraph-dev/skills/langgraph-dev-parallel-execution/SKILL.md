---
name: parallel-execution-in-langgraph
description: This skill should be used when the user asks about "parallel execution", "fan-out", "fan-in", "parallel nodes", "concurrent execution", "supersteps", "state reducers", "Send API", "deferred nodes", or needs guidance on executing multiple nodes simultaneously in LangGraph.
version: 0.3.0
---

# Parallel Execution in LangGraph

Parallel execution allows multiple nodes to process state concurrently, with results automatically merged using state reducers.

## Fan-Out/Fan-In Pattern

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Overwrite
import operator

class State(TypedDict):
    results: Annotated[list, operator.add]  # Accumulates results via concatenation
    input_data: str

def branch_1(state: State) -> dict:
    return {"results": [1, 2, 3]}

def branch_2(state: State) -> dict:
    return {"results": [4, 5, 6]}

def branch_3(state: State) -> dict:
    return {"results": [7, 8, 9]}

def combine_results(state: State) -> dict:
    """
    Process aggregated results from parallel branches.

    Note: Results are already combined by the state reducer (operator.add).
    This node performs post-processing (sorting) and uses Overwrite to
    replace the accumulated results rather than appending to them.
    """
    sorted_results = sorted(state["results"])
    return {"results": Overwrite(value=sorted_results)}

def fan_out(state: State) -> list[str]:
    """Route to multiple branches for parallel execution."""
    return ["branch_1", "branch_2", "branch_3"]

workflow = StateGraph(State)
workflow.add_node("branch_1", branch_1)
workflow.add_node("branch_2", branch_2)
workflow.add_node("branch_3", branch_3)
workflow.add_node("combine", combine_results)

# Fan-out from START to parallel branches (path_map ensures correct visualization)
workflow.add_conditional_edges(START, fan_out, ["branch_1", "branch_2", "branch_3"])

# Fan-in: all branches must complete before combine (list syntax)
workflow.add_edge(["branch_1", "branch_2", "branch_3"], "combine")
workflow.add_edge("combine", END)

# Compile the graph before invocation
graph = workflow.compile()

# Invoke the graph
result = graph.invoke({"input_data": "test", "results": []})
```

Result: `result["results"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]` (sorted by `combine_results` after accumulation)

## Dynamic Fan-Out with Send API

The `Send` API enables dynamic parallelism where the number of parallel tasks is determined at runtime.

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
import operator

class OverallState(TypedDict):
    subjects: list[str]
    jokes: Annotated[list[str], operator.add]

class JokeState(TypedDict):
    subject: str

def generate_joke(state: JokeState) -> dict:
    """Process a single subject - runs in parallel for each Send."""
    return {"jokes": [f"Why did the {state['subject']} cross the road?"]}

def continue_to_jokes(state: OverallState) -> list[Send]:
    """Create dynamic parallel tasks for each subject."""
    return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]

workflow = StateGraph(OverallState)
workflow.add_node("generate_joke", generate_joke)
workflow.add_conditional_edges(START, continue_to_jokes, ["generate_joke"])
workflow.add_edge("generate_joke", END)

graph = workflow.compile()
result = graph.invoke({"subjects": ["cat", "dog", "bird"], "jokes": []})
# result["jokes"] contains 3 jokes processed in parallel
```

Key benefits of Send API:
- Number of parallel tasks determined at runtime
- Each task can receive different state
- Ideal for map-reduce patterns where input count varies

## Deferred Execution (Synchronization Barriers)

Use `defer=True` to delay node execution until all parallel branches complete.

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Overwrite
import operator

class State(TypedDict):
    results: Annotated[list, operator.add]

def branch_1(state: State) -> dict:
    """First parallel branch."""
    return {"results": [1, 2, 3]}

def branch_2(state: State) -> dict:
    """Second parallel branch."""
    return {"results": [4, 5, 6]}

def aggregate_results(state: State) -> dict:
    """Runs only after ALL parallel branches complete.

    Uses Overwrite to replace accumulated results with final aggregate.
    """
    total = sum(state["results"])
    return {"results": Overwrite(value=[total])}

workflow = StateGraph(State)
workflow.add_node("branch_1", branch_1)
workflow.add_node("branch_2", branch_2)
# Deferred node waits for all pending tasks
workflow.add_node("aggregate", aggregate_results, defer=True)

workflow.add_conditional_edges(START, lambda s: ["branch_1", "branch_2"], ["branch_1", "branch_2"])
workflow.add_edge(["branch_1", "branch_2"], "aggregate")
workflow.add_edge("aggregate", END)

graph = workflow.compile()
```

When `defer=True`:
- Node waits for all pending tasks to complete
- Creates explicit synchronization barrier
- Prevents race conditions in map-reduce workflows

Use cases:
- **Map-Reduce**: Wait for all parallel processors before aggregation
- **Consensus**: Collect results from multiple agents before decision
- **Multi-Agent**: Coordinate branches with asymmetric completion times

## State Reducers

Reducers control how parallel updates merge:

```python
from typing import Annotated, TypedDict
import operator

def merge_unique(existing: list, new: list) -> list:
    """Custom reducer that only adds unique items."""
    seen = set(existing)
    return existing + [x for x in new if x not in seen]

class State(TypedDict):
    # Concatenate lists (using operator.add)
    results: Annotated[list, operator.add]

    # Custom reducer for unique values
    unique_items: Annotated[list, merge_unique]
```

## Bypassing Reducers with Overwrite

When post-processing accumulated results, use `Overwrite` to replace rather than append:

```python
from langgraph.types import Overwrite

def post_process(state: State) -> dict:
    """Replace accumulated results with processed version."""
    processed = sorted(state["results"])
    return {"results": Overwrite(value=processed)}
```

Key points:
- Bypasses the reducer and directly sets the channel value
- Cannot have multiple `Overwrite` values for same key in a single superstep
- Use for aggregation/post-processing nodes, not parallel branches

## Supersteps

Parallel nodes execute in "supersteps":
- All parallel nodes start simultaneously
- All must complete before workflow continues
- Transactional: If one fails, none of the updates are applied to state
- With checkpointing: Successful nodes are saved internally and don't repeat on retry
- Only failing branches retry, preventing redundant work

## Deterministic Ordering

To maintain stable ordering across parallel executions, use a factory function pattern since LangGraph node functions only accept state as a parameter:

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Overwrite
import operator

class State(TypedDict):
    results: Annotated[list, operator.add]
    input_data: str

def create_branch(branch_id: int):
    """Factory function that creates branch functions with captured branch_id."""
    def branch(state: State) -> dict:
        result = f"processed_{branch_id}"
        return {"results": [(branch_id, result)]}
    return branch

def combine(state: State) -> dict:
    """Sort results by branch_id for deterministic ordering.

    Uses Overwrite to replace accumulated (branch_id, result) tuples
    with the final ordered results list.
    """
    sorted_results = sorted(state["results"], key=lambda x: x[0])
    return {"results": Overwrite(value=[x[1] for x in sorted_results])}

# Complete example with factory function:
workflow = StateGraph(State)
workflow.add_node("branch_1", create_branch(1))
workflow.add_node("branch_2", create_branch(2))
workflow.add_node("branch_3", create_branch(3))
workflow.add_node("combine", combine)

# Fan-out to parallel branches
workflow.add_conditional_edges(
    START,
    lambda s: ["branch_1", "branch_2", "branch_3"],
    ["branch_1", "branch_2", "branch_3"]
)

# Fan-in: all branches complete before combine
workflow.add_edge(["branch_1", "branch_2", "branch_3"], "combine")
workflow.add_edge("combine", END)

graph = workflow.compile()
result = graph.invoke({"input_data": "test", "results": []})
# result["results"] = ["processed_1", "processed_2", "processed_3"] (deterministically ordered)
```

## Error Handling in Parallel

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph
from langgraph.types import RetryPolicy
import operator

class State(TypedDict):
    input_data: str
    results: Annotated[list, operator.add]
    errors: Annotated[list, operator.add]

def process_data(input_data: str) -> str:
    """Example processing function."""
    return f"processed_{input_data}"

# Option 1: Manual error handling per branch
def safe_branch(state: State) -> dict:
    try:
        result = process_data(state["input_data"])
        return {"results": [result], "errors": []}
    except Exception as e:
        return {"results": [], "errors": [str(e)]}

# Option 2: Automatic retry with RetryPolicy
def branch_with_retry(state: State) -> dict:
    """Branch that may fail and needs retry."""
    result = process_data(state["input_data"])
    return {"results": [result], "errors": []}

workflow = StateGraph(State)
workflow.add_node(
    "branch_with_retry",
    branch_with_retry,
    retry_policy=RetryPolicy(max_attempts=3, backoff_factor=2.0)
)
```

RetryPolicy options:
- `max_attempts`: Total retry attempts (default: 3)
- `initial_interval`: Seconds before first retry (default: 0.5)
- `backoff_factor`: Multiplier per retry (default: 2.0)
- `max_interval`: Maximum wait between retries (default: 128.0)
- `jitter`: Add randomization to intervals (default: True)

## Use Cases

- Process multiple documents simultaneously
- Query multiple APIs in parallel
- Run multiple analysis pipelines
- Distribute work across specialized agents
- Map-reduce operations with dynamic task counts

## Best Practices

1. **Use reducers** - Always specify how to merge parallel updates
2. **Independent branches** - Ensure branches don't depend on each other's results
3. **Handle failures** - Implement error handling per branch or use RetryPolicy
4. **Limit parallelism** - Use `max_concurrency` in config to throttle:
   ```python
   result = graph.invoke({"input_data": "test", "results": []}, config={"max_concurrency": 5})
   ```
5. **Use defer for aggregation** - Add `defer=True` to nodes that must wait for all branches
6. **Use Send for dynamic parallelism** - When task count is determined at runtime
7. **Use Overwrite for post-processing** - Wrap return values with `Overwrite()` to replace accumulated results

## Official Documentation

- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph Use Guide](https://docs.langchain.com/oss/python/langgraph/use-graph-api)
- [LangGraph Reference - StateGraph](https://reference.langchain.com/python/langgraph/graphs/)
- [LangGraph Reference - Types (Send, RetryPolicy, Overwrite)](https://reference.langchain.com/python/langgraph/types/)
