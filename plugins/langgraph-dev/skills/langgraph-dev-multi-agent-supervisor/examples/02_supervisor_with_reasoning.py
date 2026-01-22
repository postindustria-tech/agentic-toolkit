"""
Supervisor with Structured Output and Reasoning

This example demonstrates a supervisor that explains its routing decisions,
useful for debugging and transparency in multi-agent systems.

Key features:
- Structured output includes reasoning field
- Logging shows why each routing decision was made
- Helps debug unexpected routing behavior

For testing, uses mock LLM responses (no API key required).
"""

import logging
from typing import TypedDict, Annotated, List, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# Configure logging to see routing decisions
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# ============================================================================
# State Definition
# ============================================================================

class SupervisorState(TypedDict):
    """State for supervisor workflow with messages and routing."""
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: str


# ============================================================================
# Routing Decision Schema with Reasoning
# ============================================================================

class RouterDecisionWithReasoning(BaseModel):
    """
    Enhanced routing decision with reasoning for debugging.

    The reasoning field helps developers understand why the supervisor
    chose a particular agent, making the system more transparent.
    """
    next_agent: str = Field(description="Name of next agent or FINISH")
    reasoning: str = Field(description="Why this agent was chosen")


# ============================================================================
# Mock LLM with Reasoning
# ============================================================================

class MockLLMWithReasoning:
    """Mock LLM that provides reasoning for routing decisions."""

    def with_structured_output(self, schema):
        """Return self to enable chaining."""
        self.schema = schema
        return self

    def invoke(self, messages: List[BaseMessage]):
        """Simulate routing with explanations."""
        # Count agent responses - if we have 2+ responses, finish
        # (Allows multi-step: research -> analysis)
        agent_responses = [msg for msg in messages if isinstance(msg, AIMessage)]
        if len(agent_responses) >= 2:
            return RouterDecisionWithReasoning(
                next_agent="FINISH",
                reasoning="Multiple agents have completed their tasks, finishing workflow"
            )

        # Find last HumanMessage (user input)
        last_user_msg = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_user_msg = msg
                break

        if not last_user_msg:
            return RouterDecisionWithReasoning(
                next_agent="FINISH",
                reasoning="No user messages found, completing workflow"
            )

        last_content = last_user_msg.content.lower()

        # Route based on keywords with reasoning
        if "research" in last_content or "search" in last_content or "find" in last_content:
            return RouterDecisionWithReasoning(
                next_agent="research",
                reasoning="Message contains research/search keywords indicating information gathering task"
            )
        elif "code" in last_content or "implement" in last_content or "write" in last_content:
            return RouterDecisionWithReasoning(
                next_agent="code",
                reasoning="Message contains code/implement keywords indicating development task"
            )
        elif "analyze" in last_content or "review" in last_content:
            return RouterDecisionWithReasoning(
                next_agent="analysis",
                reasoning="Message requests analysis or review"
            )
        else:
            return RouterDecisionWithReasoning(
                next_agent="FINISH",
                reasoning="No specific task keywords found, completing workflow"
            )


# Initialize mock LLM
llm = MockLLMWithReasoning()


# ============================================================================
# Supervisor Prompt
# ============================================================================

SUPERVISOR_PROMPT = """You are a supervisor coordinating specialized agents.
Available agents:
- research: Find information and answer questions
- code: Write and review code
- analysis: Analyze data and provide insights
- FINISH: Task is complete

Analyze the conversation and decide which agent to use next."""


# ============================================================================
# Supervisor Node with Reasoning
# ============================================================================

def supervisor_with_reasoning(state: SupervisorState) -> dict:
    """
    Supervisor that logs routing decisions with reasoning.

    This transparency helps debug multi-agent systems and understand
    the supervisor's decision-making process.
    """
    messages = [
        SystemMessage(content=SUPERVISOR_PROMPT),
        *state["messages"]
    ]
    router = llm.with_structured_output(RouterDecisionWithReasoning)
    decision = router.invoke(messages)

    # Log the decision with reasoning for debugging
    logger.info(f"Routing to {decision.next_agent}: {decision.reasoning}")

    return {"next_agent": decision.next_agent}


# ============================================================================
# Agent Nodes
# ============================================================================

def research_agent(state: SupervisorState) -> dict:
    """Research agent with detailed response."""
    result = AIMessage(
        content="Research results: Compiled information from documentation and examples.",
        name="research"
    )
    logger.info("Research agent completed task")
    return {"messages": [result]}


def code_agent(state: SupervisorState) -> dict:
    """Code agent with implementation details."""
    result = AIMessage(
        content="Implementation: Generated code following best practices.",
        name="code"
    )
    logger.info("Code agent completed task")
    return {"messages": [result]}


def analysis_agent(state: SupervisorState) -> dict:
    """Analysis agent for data review."""
    result = AIMessage(
        content="Analysis: Identified key patterns and insights from the data.",
        name="analysis"
    )
    logger.info("Analysis agent completed task")
    return {"messages": [result]}


# ============================================================================
# Routing Function
# ============================================================================

AgentName = Literal["research", "code", "analysis", "FINISH"]

def route_to_agent(state: SupervisorState) -> AgentName:
    """Route to next agent with validation."""
    next_agent = state["next_agent"]
    valid_agents = ("research", "code", "analysis", "FINISH")

    if next_agent not in valid_agents:
        logger.warning(f"Unexpected agent '{next_agent}', defaulting to FINISH")
        return "FINISH"

    return next_agent  # type: ignore


# ============================================================================
# Graph Construction
# ============================================================================

def create_supervisor_graph():
    """Build supervisor workflow with reasoning."""
    workflow = StateGraph(SupervisorState)

    # Add nodes
    workflow.add_node("supervisor", supervisor_with_reasoning)
    workflow.add_node("research", research_agent)
    workflow.add_node("code", code_agent)
    workflow.add_node("analysis", analysis_agent)

    # Add edges
    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "research": "research",
            "code": "code",
            "analysis": "analysis",
            "FINISH": END
        }
    )

    # All agents return to supervisor
    workflow.add_edge("research", "supervisor")
    workflow.add_edge("code", "supervisor")
    workflow.add_edge("analysis", "supervisor")

    return workflow.compile()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    app = create_supervisor_graph()

    # Test Case 1: Research then analysis
    print("=" * 70)
    print("Test Case 1: Multi-step workflow (research → analysis)")
    print("=" * 70)
    result = app.invoke({
        "messages": [
            HumanMessage(content="Please find information on LangGraph patterns"),
            HumanMessage(content="Now analyze the results")
        ],
        "next_agent": ""
    })
    print("\nFinal messages:")
    for msg in result["messages"]:
        name = getattr(msg, "name", "user")
        print(f"  [{name}]: {msg.content[:60]}...")

    # Test Case 2: Code task
    print("\n" + "=" * 70)
    print("Test Case 2: Code implementation")
    print("=" * 70)
    result = app.invoke({
        "messages": [HumanMessage(content="Write a function to parse JSON")],
        "next_agent": ""
    })
    print("\nFinal messages:")
    for msg in result["messages"]:
        name = getattr(msg, "name", "user")
        print(f"  [{name}]: {msg.content[:60]}...")

    # Test Case 3: Direct finish
    print("\n" + "=" * 70)
    print("Test Case 3: No action needed")
    print("=" * 70)
    result = app.invoke({
        "messages": [HumanMessage(content="Thanks, all done")],
        "next_agent": ""
    })
    print("\nFinal messages:")
    for msg in result["messages"]:
        name = getattr(msg, "name", "user")
        print(f"  [{name}]: {msg.content[:60]}...")

    print("\n" + "=" * 70)
    print("✓ All test cases completed with reasoning logged")
    print("=" * 70)
