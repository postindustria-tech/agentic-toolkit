"""
Basic Multi-Agent Supervisor Pattern

This example demonstrates the simplest supervisor pattern with two agents:
- research_agent: Simulates research tasks
- code_agent: Simulates coding tasks

The supervisor routes tasks based on content, using a simple pattern.
For testing, uses mock LLM responses (no API key required).
"""

from typing import TypedDict, Annotated, List, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# ============================================================================
# State Definition
# ============================================================================

class SupervisorState(TypedDict):
    """State for supervisor workflow with messages and routing."""
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: str


# ============================================================================
# Routing Decision Schema
# ============================================================================

class RouterDecision(BaseModel):
    """Supervisor's routing decision."""
    next_agent: str = Field(description="Name of next agent or FINISH")


# ============================================================================
# Mock LLM for Testing (No API Key Required)
# ============================================================================

class MockLLM:
    """Mock LLM that simulates routing decisions for testing."""

    def with_structured_output(self, schema):
        """Return self to enable chaining."""
        self.schema = schema
        return self

    def invoke(self, messages: List[BaseMessage]):
        """Simulate routing based on last user message content."""
        # Check if there's at least one agent response (AIMessage)
        # If yes, the task is complete
        has_agent_response = any(isinstance(msg, AIMessage) for msg in messages)
        if has_agent_response:
            return RouterDecision(next_agent="FINISH")

        # Find last HumanMessage (user input)
        last_user_msg = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user_msg = msg
                break

        if not last_user_msg:
            return RouterDecision(next_agent="FINISH")

        last_content = last_user_msg.content.lower()

        # Simple keyword-based routing
        if "research" in last_content or "search" in last_content:
            return RouterDecision(next_agent="research")
        elif "code" in last_content or "implement" in last_content:
            return RouterDecision(next_agent="code")
        else:
            return RouterDecision(next_agent="FINISH")


# Initialize mock LLM
llm = MockLLM()


# ============================================================================
# Supervisor Node
# ============================================================================

def supervisor_node(state: SupervisorState) -> dict:
    """
    Supervisor makes routing decisions based on conversation.

    Uses structured output to get next agent name.
    """
    router_llm = llm.with_structured_output(RouterDecision)
    decision = router_llm.invoke(state["messages"])
    return {"next_agent": decision.next_agent}


# ============================================================================
# Agent Nodes
# ============================================================================

def research_agent(state: SupervisorState) -> dict:
    """
    Research agent simulates information gathering.

    In production, would use tools like web_search, database_query, etc.
    """
    result = AIMessage(
        content="Research complete: Found relevant information on the topic.",
        name="research"
    )
    return {"messages": [result]}


def code_agent(state: SupervisorState) -> dict:
    """
    Code agent simulates code generation.

    In production, would use tools like code_interpreter, file_write, etc.
    """
    result = AIMessage(
        content="Code implementation complete: Generated solution.",
        name="code"
    )
    return {"messages": [result]}


# ============================================================================
# Routing Function
# ============================================================================

AgentName = Literal["research", "code", "FINISH"]

def route_to_agent(state: SupervisorState) -> AgentName:
    """Route to next agent based on supervisor decision."""
    next_agent = state["next_agent"]
    if next_agent not in ("research", "code", "FINISH"):
        return "FINISH"  # Safe fallback
    return next_agent  # type: ignore


# ============================================================================
# Graph Construction
# ============================================================================

def create_supervisor_graph():
    """Build and compile supervisor workflow."""
    workflow = StateGraph(SupervisorState)

    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("research", research_agent)
    workflow.add_node("code", code_agent)

    # Add edges
    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {"research": "research", "code": "code", "FINISH": END}
    )

    # Agents return to supervisor for next decision
    workflow.add_edge("research", "supervisor")
    workflow.add_edge("code", "supervisor")

    return workflow.compile()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    app = create_supervisor_graph()

    # Test Case 1: Research task
    print("=" * 70)
    print("Test Case 1: Research Task")
    print("=" * 70)
    result = app.invoke({
        "messages": [HumanMessage(content="I need research on LangGraph patterns")],
        "next_agent": ""
    })
    print("\nFinal messages:")
    for msg in result["messages"]:
        name = getattr(msg, "name", "user")
        print(f"  [{name}]: {msg.content}")

    # Test Case 2: Code task
    print("\n" + "=" * 70)
    print("Test Case 2: Code Task")
    print("=" * 70)
    result = app.invoke({
        "messages": [HumanMessage(content="Please implement a sorting algorithm")],
        "next_agent": ""
    })
    print("\nFinal messages:")
    for msg in result["messages"]:
        name = getattr(msg, "name", "user")
        print(f"  [{name}]: {msg.content}")

    # Test Case 3: Non-specific task
    print("\n" + "=" * 70)
    print("Test Case 3: Generic Task")
    print("=" * 70)
    result = app.invoke({
        "messages": [HumanMessage(content="Thank you")],
        "next_agent": ""
    })
    print("\nFinal messages:")
    for msg in result["messages"]:
        name = getattr(msg, "name", "user")
        print(f"  [{name}]: {msg.content}")

    print("\n" + "=" * 70)
    print("✓ All test cases completed successfully")
    print("=" * 70)
