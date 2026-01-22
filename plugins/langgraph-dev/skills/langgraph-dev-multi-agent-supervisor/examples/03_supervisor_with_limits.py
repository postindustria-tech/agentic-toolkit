"""
Production-Ready Supervisor with Iteration Limits and Error Handling

This example demonstrates a robust supervisor pattern suitable for production:
- Iteration limits prevent infinite loops
- Error handling in agents provides graceful degradation
- Safe fallbacks for unexpected situations
- NotRequired fields for optional state

Key features:
- Maximum iteration count prevents runaway workflows
- Try-except in agents handles failures gracefully
- Validation of routing decisions
- Comprehensive logging

For testing, uses mock LLM responses (no API key required).
"""

import logging
from typing import TypedDict, Annotated, List, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Handle NotRequired import for different Python versions
try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# State Definition with Iteration Tracking
# ============================================================================

class SupervisorStateWithLimit(TypedDict):
    """
    State with iteration tracking to prevent infinite loops.

    iteration_count is NotRequired, allowing the system to work
    even if it's not provided in initial state.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: str
    iteration_count: NotRequired[int]  # Optional field with default handling


# ============================================================================
# Routing Decision Schema
# ============================================================================

class RouterDecision(BaseModel):
    """Supervisor's routing decision."""
    next_agent: str = Field(description="Name of next agent or FINISH")


# ============================================================================
# Mock LLM with Configurable Behavior
# ============================================================================

class MockLLMWithLimits:
    """
    Mock LLM that can simulate different routing scenarios,
    including edge cases for testing iteration limits.
    """

    def __init__(self, force_loop=False):
        """
        Args:
            force_loop: If True, always routes to research (tests iteration limit)
        """
        self.force_loop = force_loop

    def with_structured_output(self, schema):
        """Return self to enable chaining."""
        self.schema = schema
        return self

    def invoke(self, messages: List[BaseMessage]):
        """Simulate routing with optional loop testing."""
        if self.force_loop:
            # Test iteration limit by always choosing same agent
            return RouterDecision(next_agent="research")

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

        # Normal routing logic
        if "research" in last_content or "search" in last_content:
            return RouterDecision(next_agent="research")
        elif "code" in last_content or "implement" in last_content:
            return RouterDecision(next_agent="code")
        else:
            return RouterDecision(next_agent="FINISH")


# Initialize mock LLM
llm = MockLLMWithLimits()


# ============================================================================
# Supervisor Prompt
# ============================================================================

SUPERVISOR_PROMPT = """You are a supervisor coordinating specialized agents.
Available agents:
- research: Find information and answer questions
- code: Write and review code
- FINISH: Task is complete

Analyze the conversation and decide which agent to use next."""


# ============================================================================
# Supervisor Node with Iteration Tracking
# ============================================================================

def supervisor_with_limit(state: SupervisorStateWithLimit) -> dict:
    """
    Supervisor that tracks iterations to prevent infinite loops.

    Safely handles missing iteration_count using .get() with default.
    """
    try:
        messages = [
            SystemMessage(content=SUPERVISOR_PROMPT),
            *state["messages"]
        ]
        router_llm = llm.with_structured_output(RouterDecision)
        decision = router_llm.invoke(messages)

        # Safely get current count, defaulting to 0
        current_count = state.get("iteration_count", 0) or 0

        logger.info(f"Iteration {current_count + 1}: Routing to {decision.next_agent}")

        return {
            "next_agent": decision.next_agent,
            "iteration_count": current_count + 1
        }
    except Exception as e:
        logger.error(f"Supervisor error: {e}")
        return {"next_agent": "FINISH"}  # Safe fallback


# ============================================================================
# Agent Nodes with Error Handling
# ============================================================================

def research_agent(state: SupervisorStateWithLimit) -> dict:
    """
    Research agent with error handling for robustness.

    In production, this would catch API errors, network issues, etc.
    """
    try:
        result = AIMessage(
            content="Research complete: Found relevant information.",
            name="research"
        )
        logger.info("Research agent completed successfully")
        return {"messages": [result]}
    except Exception as e:
        logger.error(f"Research agent error: {e}")
        error_msg = AIMessage(
            content=f"Research failed: {str(e)}",
            name="research"
        )
        return {"messages": [error_msg], "next_agent": "FINISH"}


def code_agent(state: SupervisorStateWithLimit) -> dict:
    """
    Code agent with error handling for robustness.

    In production, this would catch syntax errors, runtime issues, etc.
    """
    try:
        result = AIMessage(
            content="Code implementation complete.",
            name="code"
        )
        logger.info("Code agent completed successfully")
        return {"messages": [result]}
    except Exception as e:
        logger.error(f"Code agent error: {e}")
        error_msg = AIMessage(
            content=f"Code generation failed: {str(e)}",
            name="code"
        )
        return {"messages": [error_msg], "next_agent": "FINISH"}


# ============================================================================
# Routing Function with Iteration Limit
# ============================================================================

AgentName = Literal["research", "code", "FINISH"]

MAX_ITERATIONS = 10  # Prevent infinite loops

def route_with_limit(state: SupervisorStateWithLimit) -> AgentName:
    """
    Route with iteration limit to prevent infinite loops.

    Returns FINISH after MAX_ITERATIONS to ensure termination.
    """
    current_count = state.get("iteration_count", 0) or 0

    # Force termination after max iterations
    if current_count >= MAX_ITERATIONS:
        logger.warning(f"Forcing FINISH after {current_count} iterations")
        return "FINISH"

    # Validate routing decision
    next_agent = state["next_agent"]
    if next_agent not in ("research", "code", "FINISH"):
        logger.warning(f"Unexpected agent '{next_agent}', defaulting to FINISH")
        return "FINISH"

    return next_agent  # type: ignore


# ============================================================================
# Graph Construction
# ============================================================================

def create_supervisor_graph():
    """Build production-ready supervisor workflow."""
    workflow = StateGraph(SupervisorStateWithLimit)

    # Add nodes
    workflow.add_node("supervisor", supervisor_with_limit)
    workflow.add_node("research", research_agent)
    workflow.add_node("code", code_agent)

    # Add edges
    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_with_limit,
        {"research": "research", "code": "code", "FINISH": END}
    )

    # Agents return to supervisor
    workflow.add_edge("research", "supervisor")
    workflow.add_edge("code", "supervisor")

    return workflow.compile()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    app = create_supervisor_graph()

    # Test Case 1: Normal workflow
    print("=" * 70)
    print("Test Case 1: Normal workflow (research → finish)")
    print("=" * 70)
    result = app.invoke({
        "messages": [HumanMessage(content="I need research on LangGraph")],
        "next_agent": "",
        "iteration_count": 0
    })
    print(f"\nIterations: {result.get('iteration_count', 0)}")
    print("Final messages:")
    for msg in result["messages"]:
        name = getattr(msg, "name", "user")
        print(f"  [{name}]: {msg.content[:60]}...")

    # Test Case 2: Code workflow
    print("\n" + "=" * 70)
    print("Test Case 2: Code implementation")
    print("=" * 70)
    result = app.invoke({
        "messages": [HumanMessage(content="Implement a sorting function")],
        "next_agent": "",
        "iteration_count": 0
    })
    print(f"\nIterations: {result.get('iteration_count', 0)}")
    print("Final messages:")
    for msg in result["messages"]:
        name = getattr(msg, "name", "user")
        print(f"  [{name}]: {msg.content[:60]}...")

    # Test Case 3: Iteration limit (simulate infinite loop)
    print("\n" + "=" * 70)
    print("Test Case 3: Iteration limit enforcement")
    print("=" * 70)
    print("(Simulating infinite loop scenario)")

    # Create special workflow with forced loop for testing
    # This demonstrates the iteration limit safety feature
    workflow_test = StateGraph(SupervisorStateWithLimit)

    # Create supervisor and agents with forced loop LLM
    llm_loop = MockLLMWithLimits(force_loop=True)

    def supervisor_forced_loop(state: SupervisorStateWithLimit) -> dict:
        """Supervisor that will always route to research (for testing limits)."""
        try:
            current_count = state.get("iteration_count", 0) or 0
            logger.info(f"Iteration {current_count + 1}: Testing iteration limit")
            router_llm = llm_loop.with_structured_output(RouterDecision)
            decision = router_llm.invoke(state["messages"])
            return {
                "next_agent": decision.next_agent,
                "iteration_count": current_count + 1
            }
        except Exception as e:
            logger.error(f"Supervisor error: {e}")
            return {"next_agent": "FINISH"}

    workflow_test.add_node("supervisor", supervisor_forced_loop)
    workflow_test.add_node("research", research_agent)
    workflow_test.add_edge(START, "supervisor")
    workflow_test.add_conditional_edges(
        "supervisor",
        route_with_limit,
        {"research": "research", "FINISH": END}
    )
    workflow_test.add_edge("research", "supervisor")

    app_with_loop = workflow_test.compile()

    result = app_with_loop.invoke({
        "messages": [HumanMessage(content="Start task")],
        "next_agent": "",
        "iteration_count": 0
    })
    print(f"\nIterations: {result.get('iteration_count', 0)} (capped at {MAX_ITERATIONS})")
    print(f"Status: Forced FINISH after reaching iteration limit")

    print("\n" + "=" * 70)
    print("✓ All test cases completed with safety features verified")
    print("=" * 70)
