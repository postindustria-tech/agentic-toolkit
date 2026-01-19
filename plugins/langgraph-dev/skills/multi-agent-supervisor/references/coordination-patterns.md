# Multi-Agent Coordination Patterns

This reference provides detailed patterns for coordinating multiple agents in LangGraph supervisor systems.

## Pattern Categories

### 1. Sequential Coordination
### 2. Parallel Coordination
### 3. Hierarchical Coordination
### 4. Collaborative Coordination

---

## 1. Sequential Coordination

**When to use**: Tasks require ordered execution where each agent depends on the previous agent's output.

**Example Use Cases**:
- Research → Analysis → Report Generation
- Data Collection → Validation → Processing
- Draft → Review → Publish

### Basic Pattern

```python
from typing import TypedDict, Annotated, List, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class SequentialState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: str
    workflow_stage: str  # Track progress

class RouterDecision(BaseModel):
    next_agent: str = Field(description="Next agent or FINISH")

def supervisor_sequential(state: SequentialState) -> dict:
    """
    Supervisor for sequential workflow.

    Routes based on workflow stage:
    - initial → research
    - research_complete → analysis
    - analysis_complete → report
    - report_complete → FINISH
    """
    stage = state.get("workflow_stage", "initial")

    stage_routing = {
        "initial": "research",
        "research_complete": "analysis",
        "analysis_complete": "report",
        "report_complete": "FINISH"
    }

    next_agent = stage_routing.get(stage, "FINISH")
    return {"next_agent": next_agent}

def research_agent(state: SequentialState) -> dict:
    """Research agent marks workflow stage after completion."""
    result = AIMessage(content="Research findings: ...", name="research")
    return {
        "messages": [result],
        "workflow_stage": "research_complete"
    }

def analysis_agent(state: SequentialState) -> dict:
    """Analysis agent processes research findings."""
    result = AIMessage(content="Analysis: ...", name="analysis")
    return {
        "messages": [result],
        "workflow_stage": "analysis_complete"
    }

# ... build graph with linear supervisor routing
```

**Key Points**:
- Use `workflow_stage` field to track progress
- Each agent updates stage after completion
- Supervisor routes based on current stage
- Ensures strict ordering of execution

---

## 2. Parallel Coordination

**When to use**: Independent tasks can execute simultaneously without dependencies.

**Example Use Cases**:
- Multiple data sources fetching concurrently
- Parallel document processing
- Simultaneous validation checks

### Basic Pattern

```python
from typing import TypedDict, Annotated, List
import operator

class ParallelState(TypedDict):
    input: str
    parallel_results: Annotated[List[dict], operator.add]  # Accumulates results
    all_complete: bool

def supervisor_parallel(state: ParallelState) -> dict:
    """
    Supervisor for parallel execution.

    Dispatches to all agents in first invocation,
    then waits for all to complete before finishing.
    """
    # Check if all agents have responded
    expected_agents = 3
    if len(state.get("parallel_results", [])) >= expected_agents:
        return {"all_complete": True}

    # First invocation: return list of agents to fan out to
    return {"all_complete": False}

def data_source_1(state: ParallelState) -> dict:
    """First parallel agent."""
    result = {"source": "db1", "data": "..."}
    return {"parallel_results": [result]}

def data_source_2(state: ParallelState) -> dict:
    """Second parallel agent."""
    result = {"source": "api", "data": "..."}
    return {"parallel_results": [result]}

def data_source_3(state: ParallelState) -> dict:
    """Third parallel agent."""
    result = {"source": "file", "data": "..."}
    return {"parallel_results": [result]}

# Build graph:
# workflow.add_node("supervisor", supervisor_parallel)
# workflow.add_node("source1", data_source_1)
# workflow.add_node("source2", data_source_2)
# workflow.add_node("source3", data_source_3)
#
# workflow.add_edge(START, "supervisor")
#
# # Fan-out to all agents
# workflow.add_edge("supervisor", "source1")
# workflow.add_edge("supervisor", "source2")
# workflow.add_edge("supervisor", "source3")
#
# # Fan-in back to supervisor
# workflow.add_edge("source1", "supervisor")
# workflow.add_edge("source2", "supervisor")
# workflow.add_edge("source3", "supervisor")
#
# # Conditional exit when all complete
# workflow.add_conditional_edges(
#     "supervisor",
#     lambda state: "end" if state.get("all_complete") else "continue",
#     {"end": END, "continue": "supervisor"}
# )
```

**Key Points**:
- Use `operator.add` reducer to accumulate parallel results
- Fan-out pattern: supervisor → all agents
- Fan-in pattern: all agents → supervisor
- Supervisor checks completion count before finishing
- Results order is not guaranteed

---

## 3. Hierarchical Coordination

**When to use**: Complex workflows with sub-workflows or nested coordination.

**Example Use Cases**:
- Team manager coordinating sub-teams
- Department workflow with specialized units
- Multi-level approval processes

### Basic Pattern

```python
from typing import TypedDict, List
from langgraph.graph import StateGraph

class DepartmentState(TypedDict):
    task: str
    department_result: str

class CompanyState(TypedDict):
    project: str
    engineering_result: str
    marketing_result: str
    final_result: str

# Engineering Department (sub-supervisor)
def create_engineering_department():
    """Sub-supervisor for engineering tasks."""
    workflow = StateGraph(DepartmentState)

    def engineering_supervisor(state: DepartmentState) -> dict:
        # Routes between backend/frontend/devops
        task = state["task"].lower()
        if "backend" in task:
            return {"next_agent": "backend"}
        elif "frontend" in task:
            return {"next_agent": "frontend"}
        else:
            return {"next_agent": "devops"}

    def backend_agent(state: DepartmentState) -> dict:
        return {"department_result": "Backend implementation complete"}

    def frontend_agent(state: DepartmentState) -> dict:
        return {"department_result": "Frontend implementation complete"}

    def devops_agent(state: DepartmentState) -> dict:
        return {"department_result": "DevOps setup complete"}

    workflow.add_node("supervisor", engineering_supervisor)
    workflow.add_node("backend", backend_agent)
    workflow.add_node("frontend", frontend_agent)
    workflow.add_node("devops", devops_agent)

    # ... add edges (similar to basic supervisor pattern)

    return workflow.compile()

# Company-level supervisor (top-level)
def company_supervisor(state: CompanyState) -> dict:
    """Top-level supervisor delegates to departments."""
    # Route to appropriate department
    project = state["project"].lower()

    if "engineering" in project:
        return {"next_department": "engineering"}
    elif "marketing" in project:
        return {"next_department": "marketing"}
    else:
        return {"next_department": "FINISH"}

# Use compiled sub-supervisors as nodes
engineering_dept = create_engineering_department()

def engineering_wrapper(state: CompanyState) -> dict:
    """Wrapper to call engineering sub-supervisor."""
    dept_result = engineering_dept.invoke({
        "task": state["project"],
        "department_result": ""
    })
    return {"engineering_result": dept_result["department_result"]}

# Top-level graph
company_workflow = StateGraph(CompanyState)
company_workflow.add_node("supervisor", company_supervisor)
company_workflow.add_node("engineering", engineering_wrapper)
# ... add other departments
```

**Key Points**:
- Each level has its own supervisor
- Sub-supervisors are compiled and used as nodes
- Wrapper functions transform state between levels
- Clear separation of concerns at each hierarchy level
- State transformation required between parent and child

---

## 4. Collaborative Coordination

**When to use**: Agents need to share information and work together on same problem.

**Example Use Cases**:
- Multiple agents contributing to shared document
- Consensus-building workflows
- Iterative refinement by multiple specialists

### Basic Pattern

```python
from typing import TypedDict, Annotated, List, Dict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class CollaborativeState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    shared_context: Dict[str, str]  # Shared workspace
    contributions: Dict[str, str]  # Track agent contributions
    iteration: int
    consensus_reached: bool

def supervisor_collaborative(state: CollaborativeState) -> dict:
    """
    Supervisor for collaborative workflow.

    Routes agents in rounds:
    - Round 1: All agents contribute initial thoughts
    - Round 2: All agents review and refine
    - Round 3: Final consensus check
    """
    iteration = state.get("iteration", 0)

    if iteration >= 3 or state.get("consensus_reached"):
        return {"next_agent": "FINISH"}

    # Rotate through agents
    agents = ["analyst", "designer", "engineer"]
    current_agent = agents[iteration % len(agents)]

    return {
        "next_agent": current_agent,
        "iteration": iteration + 1
    }

def analyst_agent(state: CollaborativeState) -> dict:
    """Analyst contributes to shared context."""
    # Read shared context from other agents
    designer_input = state["shared_context"].get("designer", "")
    engineer_input = state["shared_context"].get("engineer", "")

    # Contribute analysis
    analysis = f"Analysis considering: {designer_input} and {engineer_input}"

    return {
        "shared_context": {**state["shared_context"], "analyst": analysis},
        "contributions": {**state["contributions"], "analyst": analysis}
    }

# Similar for designer_agent and engineer_agent
# Each reads shared_context and contributes back
```

**Key Points**:
- `shared_context` dict allows agents to see each other's work
- Agents read from shared context before contributing
- Multiple rounds enable iterative refinement
- Consensus check determines completion

---

## Pattern Selection Guide

| Pattern | Dependencies | Execution | Communication | Complexity |
|---------|--------------|-----------|---------------|------------|
| **Sequential** | Strong (ordered) | Series | One-way | Low |
| **Parallel** | None | Concurrent | Independent | Medium |
| **Hierarchical** | Nested | Delegated | Parent-child | High |
| **Collaborative** | Shared context | Iterative | Bidirectional | High |

**Decision Tree**:
1. Do tasks have dependencies?
   - Yes → Sequential or Hierarchical
   - No → Parallel
2. Do agents need to share information?
   - Yes → Collaborative
   - No → Sequential or Parallel
3. Is there a natural hierarchy?
   - Yes → Hierarchical
   - No → Sequential or Collaborative

---

## Combining Patterns

Real-world systems often combine multiple patterns:

```python
# Example: Hierarchical + Sequential + Parallel
#
# Company Supervisor (Hierarchical)
#   ├── Engineering Dept (Sequential)
#   │     ├── Design → Implementation → Testing
#   │     └── Each phase uses Parallel for sub-tasks
#   └── Marketing Dept (Collaborative)
#         └── Multiple stakeholders refine campaign
```

**Best Practice**: Start simple (Sequential), add complexity only when needed.

---

## References

- LangGraph Documentation: https://docs.langchain.com/oss/python/langgraph/
- Multi-Agent Guide: https://docs.langchain.com/oss/python/langchain/multi-agent/
- See `SKILL.md` for basic supervisor pattern
- See `examples/` for working code demonstrations
