---
name: react-agents-in-langgraph
description: This skill should be used when the user asks about "ReAct agent", "reasoning agent", "thought action observation", "ReAct pattern", "agent loop", or needs guidance on building ReAct-style agents with LangGraph.
version: 0.5.0
---

# ReAct Agents in LangGraph

> **Note**: This skill targets LangGraph v1.0+ (released October 2025). The `create_react_agent` function from `langgraph.prebuilt` is deprecated in favor of `langchain.agents.create_agent`. However, `create_react_agent` remains functional for existing code. For new projects, use `from langchain.agents import create_agent` (requires LangChain >= 1.0).

ReAct (Reasoning + Acting) is a pattern where LLMs iteratively reason about tasks, select actions (tools), observe results, and continue until reaching a final answer.

## ReAct Loop Pattern

**Thought** -> **Action** -> **Observation** -> Repeat until **Final Answer**

## Quick Start with Prebuilt Agent

For rapid prototyping, use the prebuilt `create_react_agent`:

```python
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

@tool
def search_tool(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

# Create model instance (recommended over string format)
model = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# Create a ReAct agent
# DEPRECATED in LangGraph v1.0: Migrate to `from langchain.agents import create_agent`
# For new projects, use: agent = create_agent(model=model, tools=[search_tool], system_prompt="You are a helpful assistant.")
agent = create_react_agent(
    model=model,
    tools=[search_tool],
    prompt="You are a helpful assistant."  # Also accepts SystemMessage, Callable, or Runnable
)

# Run the agent
result = agent.invoke({"messages": [("user", "Search for LangGraph docs")]})
```

> **Model Options**: Pass a model instance (`ChatAnthropic`, `ChatOpenAI`) or use string format `"provider:model-name"` (e.g., `"openai:gpt-4o"`).
>
> **Prompt Flexibility**: The `prompt` parameter accepts: string, `SystemMessage`, `Callable[[list[BaseMessage]], list[BaseMessage]]`, or `Runnable`.

## Custom Implementation (From Scratch)

For full control over the agent loop, build a custom ReAct graph:

```python
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

# Define state with add_messages reducer
class AgentState(TypedDict):
    """The state of the agent."""
    messages: Annotated[list[BaseMessage], add_messages]

# Alternative: Use prebuilt MessagesState (includes add_messages reducer):
# from langgraph.graph import MessagesState
# workflow = StateGraph(MessagesState)  # No need to define custom AgentState

# Define tools using @tool decorator
@tool
def search_tool(query: str) -> str:
    """Search the web for information.

    Args:
        query: A search query string.
    """
    return f"Results for: {query}"

@tool
def calculator_tool(expression: str) -> str:
    """Perform arithmetic calculations safely.

    Args:
        expression: A math expression like '2+2', '10*5', or 'sqrt(144)'

    Returns:
        The numerical result as a string.
    """
    import math
    from simpleeval import simple_eval  # AST-based safe math parser

    # Define safe math functions
    safe_functions = {
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
        "pow": pow,
        "min": min,
        "max": max,
    }

    try:
        result = simple_eval(expression, functions=safe_functions)
        return str(float(result))
    except Exception as e:
        return f"Error: {e}"

tools = [search_tool, calculator_tool]

# Initialize LLM and bind tools
llm = ChatOpenAI(model="gpt-4.1-mini")  # or: ChatAnthropic(model="claude-sonnet-4-5-20250929")
llm_with_tools = llm.bind_tools(tools)

# Agent node: Generates thought and action
# The optional config parameter provides thread_id, tags, and other runtime info
def agent_node(state: AgentState, config: RunnableConfig | None = None) -> dict:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# Tool node: Executes action, returns observation
tool_node = ToolNode(tools)

# Routing: Use prebuilt tools_condition or custom function
# Option 1: Use prebuilt tools_condition (recommended)
# tools_condition returns "tools" if tool_calls present, or "__end__" to terminate
# Note: "__end__" is the string literal; use END constant in edge mappings

# Option 2: Custom routing with standard return values
def should_continue(state: AgentState) -> str:
    """Route to tools if tool calls present, otherwise end."""
    messages = state["messages"]
    if not messages:
        return "__end__"  # No messages to process
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# Modern pattern: use START constant
workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,  # Or use: tools_condition
    {"tools": "tools", "__end__": END}
)
workflow.add_edge("tools", "agent")  # Loop back

app = workflow.compile()
```

## Execution

### Synchronous Invocation

```python
# Run the agent
result = app.invoke({"messages": [("user", "Search for LangGraph docs")]})
print(result["messages"][-1].content)
```

### Asynchronous Invocation

```python
# Async execution (recommended for production)
result = await app.ainvoke({"messages": [("user", "Search for LangGraph docs")]})

# Async streaming
async for chunk in app.astream({"messages": [("user", "Hello")]}):
    print(chunk)
```

### With Recursion Limit

```python
# Prevent infinite loops by setting recursion_limit
result = app.invoke(
    {"messages": [("user", "Complex multi-step query")]},
    {"recursion_limit": 25}  # Default is 25, adjust as needed
)
```

## Execution Flow

1. **Model generates response**: LLM analyzes task, decides if tools needed
2. **Tool calls extracted**: If tools needed, AIMessage contains tool_calls
3. **Tools execute**: ToolNode runs requested tools
4. **Tool results returned**: Results added to messages as ToolMessage objects
5. **Loop**: Back to step 1 until model decides task complete (no tool_calls)

## Tool Definition Best Practices

LLM selects tools based on their descriptions. Write clear, specific descriptions:

```python
from langchain_core.tools import tool

# Good tool description - clear purpose and input format
@tool
def calculator_tool(expression: str) -> str:
    """Perform arithmetic calculations safely.

    Args:
        expression: A math expression like '2+2', '10*5', or 'sqrt(144)'

    Returns:
        The numerical result as a string.
    """
    import math
    from simpleeval import simple_eval  # AST-based safe math parser

    safe_functions = {
        "sqrt": math.sqrt,
        "abs": abs,
        "round": round,
        "pow": pow,
    }

    try:
        result = simple_eval(expression, functions=safe_functions)
        return str(float(result))
    except Exception as e:
        return f"Error: {e}"

# Bad tool description (avoid vague descriptions)
@tool
def tool1(input_str: str) -> str:
    """Does stuff"""  # Too vague! Model won't know when to use this
    return input_str
```

## Example Interaction

```
User: "What is the square root of 144?"

Thought: Need to calculate square root
Action: calculator_tool("sqrt(144)")
Observation: 12.0

Thought: Have the answer
Final Answer: The square root of 144 is 12.
```

## Zero-Shot vs Few-Shot

**Zero-Shot**: Agent decides tool use without examples - relies on tool descriptions
**Few-Shot**: Provide example reasoning traces in system prompt for guidance

## Best Practices

1. **Limit iterations** - Use `recursion_limit` config to prevent infinite loops:
   ```python
   result = app.invoke(state, {"recursion_limit": 25})
   ```
2. **Clear tool descriptions** - Help LLM select correct tools with specific descriptions
3. **Use async for production** - Prefer `ainvoke()` and `astream()` for scalability
4. **Handle no-tool case** - Ensure agent can answer without tools when appropriate
5. **Safe tool implementations** - Use simpleeval or AST-based parsing for math expressions (avoid sympify with untrusted input)
6. **Use prebuilt utilities** - Prefer `tools_condition` over custom routing when possible

## Resources

- [LangGraph ReAct from Scratch](https://langchain-ai.github.io/langgraph/how-tos/react-agent-from-scratch/)
- [LangGraph Agents API Reference](https://reference.langchain.com/python/langgraph/agents/)
- [LangChain Tools Reference](https://reference.langchain.com/python/langchain/tools/)
