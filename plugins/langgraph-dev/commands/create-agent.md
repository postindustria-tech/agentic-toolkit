---
name: create-agent
description: Generate a ReAct agent with ToolNode integration and tool calling
argument-hint: agent_name [--tools=tool1,tool2,tool3]
allowed-tools:
  - Read
  - Write
  - AskUserQuestion
---

# Create ReAct Agent

Generate a complete ReAct agent with tool calling, ToolNode integration, and conditional routing.

## Instructions for Claude

### 1. Gather Requirements

Ask user for:
- Agent name (if not provided)
- Tools to include (if `--tools` not provided):
  - Search (web search)
  - Calculator (math operations)
  - Custom tools (user-defined)
- Purpose/domain of the agent

### 2. Read Settings

Check `.claude/langgraph-dev.local.md` for:
- `llm_provider` and `llm_model`
- `async_by_default`
- Code style preferences

### 3. Generate Agent Structure

Create:
```
{agent_name}/
├── agent.py        # ReAct agent implementation
├── tools.py        # Tool definitions
├── state.py        # Agent state schema
└── README.md
```

### 4. Generate state.py

```python
from typing import TypedDict, Annotated, List
from langchain.schema import BaseMessage
import operator

class AgentState(TypedDict):
    \"\"\"State for ReAct agent.\"\"\"
    messages: Annotated[List[BaseMessage], operator.add]
```

### 5. Generate tools.py

```python
from langchain.tools import Tool

def search_web(query: str) -> str:
    \"\"\"Search the web for information.\"\"\"
    # Implementation
    return f"Search results for: {query}"

search_tool = Tool(
    name="WebSearch",
    func=search_web,
    description="Useful for finding current information. Input: search query."
)

# Add other tools based on user selection
tools = [search_tool, ...]
```

### 6. Generate agent.py

```python
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic
from .tools import tools
from .state import AgentState

# LLM with tools
llm = ChatAnthropic(model="claude-sonnet-4-5")
llm_with_tools = llm.bind_tools(tools)

# Agent node
def agent_node(state: AgentState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# Tool execution node
tool_node = ToolNode(tools)

# Routing logic
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    END: END
})
workflow.add_edge("tools", "agent")  # Loop back

app = workflow.compile()
```

### 7. Generate README.md

Include:
- Agent description and purpose
- Tools available
- Usage examples
- Environment setup

### 8. Output Summary

Show:
- Files created
- Tools included
- Example usage:
  ```python
  result = app.invoke({"messages": [HumanMessage(content="Search for Python tutorials")]})
  ```

## Example Invocation

```
/langgraph-dev:create-agent research-agent --tools=search,calculator
```

Refer to **react-agents** and **tool-calling** skills for patterns.
