"""LangGraph workflow with context schema for assistants."""

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Runtime
from langchain_anthropic import ChatAnthropic

from .agent_state import AgentState


class ContextSchema(TypedDict):
    """Configuration schema for assistant variants.

    This allows creating multiple assistants with different configurations
    from the same graph structure.
    """
    model_name: str  # "claude-3-5-sonnet-20241022" or "claude-3-5-haiku-20241022"
    temperature: float  # 0.0 - 1.0
    max_tokens: int  # Max response tokens


def call_model(state: AgentState, runtime: Runtime[ContextSchema]) -> dict:
    """Call LLM with configuration from runtime context.

    Args:
        state: Current agent state
        runtime: Runtime with context configuration

    Returns:
        State update with LLM response
    """
    # Get configuration from runtime context
    model_name = runtime.context.get("model_name", "claude-3-5-sonnet-20241022")
    temperature = runtime.context.get("temperature", 0.7)
    max_tokens = runtime.context.get("max_tokens", 1024)

    # Initialize LLM with configuration
    llm = ChatAnthropic(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens
    )

    # Invoke LLM
    response = llm.invoke(state["messages"])

    return {
        "messages": [response],
        "current_step": "completed"
    }


def create_graph():
    """Create production-ready graph with context schema.

    Returns:
        Compiled graph ready for deployment
    """
    # Build graph with context schema
    builder = StateGraph(AgentState, context_schema=ContextSchema)

    # Add nodes
    builder.add_node("call_model", call_model)

    # Add edges
    builder.add_edge(START, "call_model")
    builder.add_edge("call_model", END)

    # Compile (checkpointer added by Platform)
    return builder.compile()


# Export for Platform deployment
graph = create_graph()
