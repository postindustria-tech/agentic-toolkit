---
name: tool-calling-in-langgraph
description: This skill should be used when the user asks about "tool calling", "ToolNode", "bind tools", "tool execution", "model.bind_tools()", "tool integration", "LangGraph tools", or needs guidance on integrating tools with LangGraph workflows.
version: 0.3.2
---

# Tool Calling in LangGraph

Tool calling enables LangGraph workflows to use external tools (APIs, functions, databases) through standardized tool nodes that execute based on LLM decisions.

## Core Pattern

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic

# Define state
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Define tools using @tool decorator
@tool
def search_function(query: str) -> str:
    """Search the web for information. Input should be a search query."""
    return f"Results for: {query}"

@tool
def calculator(a: int, b: int) -> int:
    """Perform mathematical calculations. Add two numbers together."""
    return a + b

tools = [search_function, calculator]

# Create tool node
tool_node = ToolNode(tools)

# Bind tools to LLM
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
llm_with_tools = llm.bind_tools(tools)

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", lambda state: {"messages": [llm_with_tools.invoke(state["messages"])]})
workflow.add_node("tools", tool_node)

# Add edges
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")

# Compile
graph = workflow.compile()
```

## ReAct Tool Loop

### Using Prebuilt tools_condition (Recommended)

```python
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# Use prebuilt condition - returns "tools" or "__end__"
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")  # Loop back after tool use
workflow.add_edge(START, "agent")

graph = workflow.compile()
```

### Custom Routing Function

```python
from langgraph.graph import StateGraph, END

def should_continue(state: AgentState):
    """Check if LLM wants to use tools."""
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    return "continue"

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    },
)
workflow.add_edge("tools", "agent")  # Loop back after tool use
```

## Tool Definition

The `@tool` decorator is the recommended way to create tools. It automatically uses the function name as the tool name and the docstring as the description.

```python
from langchain_core.tools import tool

@tool
def search_web(query: str) -> str:
    """Useful for finding current information on the web.
    Input should be a search query string."""
    return f"Results for: {query}"

@tool
def get_weather(location: str) -> str:
    """Get the current weather for a specific location.
    Input should be a city name or location."""
    if "san francisco" in location.lower():
        return "It's sunny in San Francisco, 72F"
    return f"Weather data for {location} not available"

# Tools are ready to use
tools = [search_web, get_weather]
```

## LLM Tool Binding

```python
from langchain_core.messages import HumanMessage
from langchain_anthropic import ChatAnthropic

# Create LLM and bind tools
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
llm_with_tools = llm.bind_tools([search_web, get_weather])

# Model can now generate tool calls
response = llm_with_tools.invoke([HumanMessage(content="What's the weather in San Francisco?")])

# response.tool_calls contains requested tool invocations (if any)
if response.tool_calls:
    print(f"Tool calls requested: {len(response.tool_calls)}")
```

## ToolNode Execution

ToolNode automatically:
1. Extracts tool calls from LLM response
2. Executes corresponding tool functions
3. Formats results as ToolMessage
4. Adds to state messages

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic

# Define state
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# Define tools
@tool
def search_function(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

tools = [search_function]
tool_node = ToolNode(tools)

# Set up LLM with tools
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
llm_with_tools = llm.bind_tools(tools)

# Define agent node
def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# Build and compile graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")
workflow.add_edge(START, "agent")

graph = workflow.compile()
```

## Parallel Tool Execution

LLMs can request multiple tools simultaneously. ToolNode executes them in parallel.

```python
# LLM can request multiple tools at once
response = llm_with_tools.invoke([message])

# response.tool_calls is a list of ToolCall TypedDict objects
# Access fields using dictionary notation
for tool_call in response.tool_calls:
    print(f"Tool: {tool_call['name']}, Args: {tool_call['args']}, ID: {tool_call['id']}")

# ToolNode automatically executes all tool calls in parallel
# and returns a list of ToolMessages
```

## Async Tool Support

ToolNode supports both synchronous and asynchronous tools.

```python
from langchain_core.tools import tool
import httpx

@tool
async def async_search(query: str) -> str:
    """Search the web asynchronously for information."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.example.com/search?q={query}")
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as e:
        return f"Search failed: {str(e)}"

# ToolNode handles async tools automatically
tools = [async_search]
tool_node = ToolNode(tools)
```

## Best Practices

1. **Clear tool descriptions** - LLM uses descriptions to decide when to use tools. Write detailed docstrings.
2. **Validate tool inputs** - Tools should handle invalid inputs gracefully
3. **Return structured output** - Consistent return formats help LLM understand results
4. **Limit tool count** - Too many tools confuse LLM selection (consider dynamic tool selection for large tool sets)
5. **Handle tool errors gracefully** - Use ToolNode's `handle_tool_errors` parameter:
   ```python
   tool_node = ToolNode(tools, handle_tool_errors=True)
   ```
6. **Use type hints** - The `@tool` decorator uses type hints to generate input schemas

## Official Documentation

- [LangGraph Quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
- [Workflows and Agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [LangGraph Agents API Reference](https://reference.langchain.com/python/langgraph/agents/)
- [LangChain Tools Documentation](https://docs.langchain.com/oss/python/langchain/tools)
- [LangChain Tools API Reference](https://reference.langchain.com/python/langchain/tools/)

## LangGraph v1.0 Compatibility

LangGraph v1.0 is a stability-focused release. The core graph APIs, including `ToolNode` and `tools_condition`, remain unchanged and fully compatible. Graph primitives (state, nodes, edges) and the execution model are stable, making upgrades straightforward.

For migration details, see [What's new in LangGraph v1](https://docs.langchain.com/oss/python/releases/langgraph-v1).
