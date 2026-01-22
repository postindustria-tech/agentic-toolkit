---
name: multi-agent-supervisor-pattern
description: This skill should be used when the user asks about "multi-agent", "supervisor pattern", "agent coordination", "orchestrate agents", "agent routing", "multi-agent system", "LLM routing", "structured output routing", or needs guidance on coordinating multiple specialized agents in LangGraph.
version: 0.5.0
---

# Multi-Agent Supervisor Pattern

The supervisor pattern uses a central LLM-based router to coordinate multiple specialized agents, delegating tasks based on requirements.

## Architecture

```
User Input -> Supervisor -> Route to Agent -> Agent Executes -> Back to Supervisor -> Repeat or Finish
```

**Reference:** [Multi-Agent Supervisor Tutorial](https://docs.langchain.com/oss/python/langgraph/workflows-agents)

**See also:** For designing supervisor state schemas and reducer functions, see the `state-management` skill.

## Implementation Pattern

```python
import logging
from typing import TypedDict, Annotated, List, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Initialize logging
logger = logging.getLogger(__name__)

# Initialize LLM (choose one based on your provider)
from langchain_anthropic import ChatAnthropic
# from langchain_openai import ChatOpenAI

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
# llm = ChatOpenAI(model="gpt-4o")

# For specialized agents (can use same or different models)
research_llm = llm
code_llm = llm

# Supervisor system prompt
SUPERVISOR_PROMPT = """You are a supervisor coordinating specialized agents.
Available agents:
- research: Find information and answer questions
- code: Write and review code
- FINISH: Task is complete

Analyze the conversation and decide which agent to use next."""

# Type alias for routing destinations
AgentName = Literal["research", "code", "FINISH"]

class RouterDecision(BaseModel):
    """Supervisor's routing decision."""
    next_agent: str = Field(description="Name of next agent or FINISH")

class SupervisorState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # Preferred reducer
    next_agent: str

# Supervisor decides routing using SystemMessage with error handling
def supervisor_node(state: SupervisorState) -> dict:
    """Supervisor makes routing decisions with error handling."""
    try:
        messages = [
            SystemMessage(content=SUPERVISOR_PROMPT),
            *state["messages"]
        ]
        router_llm = llm.with_structured_output(RouterDecision)
        decision = router_llm.invoke(messages)
        return {"next_agent": decision.next_agent}
    except Exception as e:
        logger.error(f"Supervisor error: {e}")
        return {"next_agent": "FINISH"}  # Safe fallback

# Specialized agents
def research_agent(state: SupervisorState) -> dict:
    """Research-specific logic."""
    result = research_llm.invoke(state["messages"])
    return {"messages": [result]}

def code_agent(state: SupervisorState) -> dict:
    """Code-specific logic."""
    result = code_llm.invoke(state["messages"])
    return {"messages": [result]}

# Routing function with validation for unexpected LLM outputs
def route_to_agent(state: SupervisorState) -> AgentName:
    """Route to next agent, validating the LLM's routing decision."""
    next_agent = state["next_agent"]
    if next_agent not in ("research", "code", "FINISH"):
        logger.warning(f"Unexpected agent '{next_agent}', defaulting to FINISH")
        return "FINISH"
    return next_agent  # type: ignore - validated above

# Build graph
workflow = StateGraph(SupervisorState)
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("research", research_agent)
workflow.add_node("code", code_agent)

# Use add_edge with START constant (modern pattern)
workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {"research": "research", "code": "code", "FINISH": END}
)
workflow.add_edge("research", "supervisor")  # Back to supervisor
workflow.add_edge("code", "supervisor")

app = workflow.compile()
```

## Agent Helper Pattern

```python
from typing import Sequence, Any, Callable
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

def create_agent_node(
    agent_name: str,
    tools: Sequence[BaseTool | Callable[..., Any] | dict[str, Any]],
    llm: BaseChatModel
):
    """Factory for agent nodes.

    Args:
        agent_name: Name identifier for the agent (appears in messages)
        tools: Sequence of tools (BaseTool, callable, or dict) available to the agent
        llm: Language model instance to use for this agent

    Returns:
        A node function that can be added to the graph
    """
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: SupervisorState) -> dict[str, list[BaseMessage]]:
        try:
            result = llm_with_tools.invoke(state["messages"])
            # Wrap output with agent name for context
            return {"messages": [AIMessage(content=result.content, name=agent_name)]}
        except Exception as e:
            logger.error(f"Agent {agent_name} error: {e}")
            return {"messages": [AIMessage(content=f"Error in {agent_name}: {str(e)}", name=agent_name)]}

    return agent_node

# Usage example:
# research_node = create_agent_node("research", [web_search], llm)
# code_node = create_agent_node("code", [run_code], llm)
```

**See also:** For creating reusable agent subgraphs and modular multi-agent architectures, see the `subgraphs-and-composition` skill.

## Structured Routing Output

```python
import logging
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)

class RouterDecisionWithReasoning(BaseModel):
    """Enhanced routing decision with reasoning for debugging."""
    next_agent: str = Field(description="Name of next agent or FINISH")
    reasoning: str = Field(description="Why this agent was chosen")

def supervisor_with_reasoning(state: SupervisorState) -> dict:
    """Supervisor with explicit reasoning for debugging and transparency."""
    messages = [
        SystemMessage(content=SUPERVISOR_PROMPT),
        *state["messages"]
    ]
    router = llm.with_structured_output(RouterDecisionWithReasoning)
    decision = router.invoke(messages)
    logger.info(f"Routing to {decision.next_agent}: {decision.reasoning}")
    return {"next_agent": decision.next_agent}
```

## Iteration Limit for Loop Prevention

```python
# Python 3.11+: from typing import NotRequired
# Python 3.10: from typing_extensions import NotRequired
try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

class SupervisorStateWithLimit(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: str
    iteration_count: NotRequired[int]  # Optional field with default handling

def supervisor_with_limit(state: SupervisorStateWithLimit) -> dict:
    """Supervisor that tracks iterations to prevent infinite loops."""
    messages = [
        SystemMessage(content=SUPERVISOR_PROMPT),
        *state["messages"]
    ]
    router_llm = llm.with_structured_output(RouterDecision)
    decision = router_llm.invoke(messages)

    # Safely get current count, defaulting to 0
    current_count = state.get("iteration_count", 0) or 0

    return {
        "next_agent": decision.next_agent,
        "iteration_count": current_count + 1
    }

def route_with_limit(state: SupervisorStateWithLimit) -> AgentName:
    """Route with iteration limit to prevent infinite loops.

    Returns FINISH after 10 iterations to ensure termination.
    """
    current_count = state.get("iteration_count", 0) or 0
    if current_count >= 10:
        logger.warning(f"Forcing FINISH after {current_count} iterations")
        return "FINISH"  # Force termination after 10 iterations
    return state["next_agent"]

# Initialize state with default iteration count
initial_state = {
    "messages": [],
    "next_agent": "",
    "iteration_count": 0
}
```

## Best Practices

1. **Clear agent roles** - Define distinct capabilities per agent
2. **Structured routing** - Use Pydantic for type-safe routing decisions
3. **Loop prevention** - Add iteration limits or cycle detection (see example above)
4. **Agent naming** - Include agent name in messages for context
5. **Error handling** - Wrap agent execution in try/except for graceful failure handling
6. **Use context_schema (not config_schema)** - As of LangGraph v1.0, `config_schema` is being soft-deprecated in favor of `context_schema` for runtime configuration that varies per invocation.

## When to Use

- Tasks require multiple specialized capabilities
- Different agents have different tools
- Complex workflows benefit from intelligent routing
- Need to combine research, coding, analysis, etc.

## Alternative: langgraph-supervisor Library

> **Note**: The LangChain team recommends using the manual supervisor pattern
> (shown above) for production use cases, as it gives more control over context
> engineering. The langgraph-supervisor library simplifies prototyping and
> standard patterns but offers less flexibility.

For simpler implementations with standard patterns, use the `langgraph-supervisor` library:

```bash
pip install langgraph-supervisor langgraph-prebuilt
```

**Requirements**: Python >= 3.10, langgraph >= 1.0.0, langgraph-supervisor >= 0.0.31

```python
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

model = ChatOpenAI(model="gpt-4o")

# Define tool functions with detailed docstrings (improves tool selection)
def add(a: float, b: float) -> float:
    """Add two numbers together.

    Use this tool when you need to perform addition of two numeric values.

    Args:
        a: The first number to add
        b: The second number to add

    Returns:
        The sum of a and b
    """
    return a + b

def web_search(query: str) -> str:
    """Search the web for information.

    Use this tool when you need to find current information from the internet.

    Args:
        query: The search query string

    Returns:
        Search results as a formatted string
    """
    return f"Search results for: {query}"

# Create specialized agents using create_react_agent
# Returns: CompiledStateGraph (already compiled, ready to invoke)
# prompt accepts: str | SystemMessage | Callable | Runnable | None
# version defaults to "v2" (parallel tool execution)
math_agent = create_react_agent(
    model=model,
    tools=[add],
    name="math_expert",
    prompt="You are a math expert. Use tools for calculations."
)

# Alternative: Use SystemMessage for more control (e.g., Anthropic prompt caching)
from langchain_core.messages import SystemMessage
research_agent = create_react_agent(
    model=model,
    tools=[web_search],
    name="research_expert",
    prompt=SystemMessage(content="You are a research expert with web access.")
)

# Create supervisor workflow
# Note: All args after 'agents' are keyword-only
workflow = create_supervisor(
    agents=[research_agent, math_agent],  # positional arg
    model=model,                           # keyword-only
    prompt="You are a team supervisor managing research and math experts."
)

# Compile and run
app = workflow.compile()

# Option 1: OpenAI dict format (auto-converted by add_messages reducer)
# Note: Works because langgraph-supervisor uses add_messages internally
result = app.invoke({
    "messages": [{"role": "user", "content": "What is 2+2?"}]
})

# Option 2: LangChain message objects (recommended)
from langchain_core.messages import HumanMessage
result = app.invoke({
    "messages": [HumanMessage(content="What is 2+2?")]
})
```

**Note:** LangChain recommends using the supervisor pattern directly via tools rather than this library for most use cases. The tool-calling approach gives more control over context engineering. See the [LangChain Multi-Agent Guide](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant) for details.

## Additional Resources

- [Multi-Agent Supervisor Tutorial](https://docs.langchain.com/oss/python/langgraph/workflows-agents) - Official LangGraph supervisor tutorial
- [Multi-Agent Guide](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents-personal-assistant) - LangChain multi-agent patterns
- [Supervisor API Reference](https://reference.langchain.com/python/langgraph/supervisor/) - LangGraph supervisor reference
- [LangGraph Agents Reference](https://reference.langchain.com/python/langgraph/agents/) - create_react_agent API
- [langgraph-supervisor GitHub Repository](https://github.com/langchain-ai/langgraph-supervisor-py) - Library source code
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api) - State management and reducers
