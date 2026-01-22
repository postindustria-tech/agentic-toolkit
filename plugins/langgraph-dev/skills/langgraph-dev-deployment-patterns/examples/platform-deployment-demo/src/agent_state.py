"""Agent state definition for Platform deployment example."""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for conversational agent.

    Attributes:
        messages: Conversation history (accumulated with add_messages reducer)
        current_step: Current processing step for observability
    """
    messages: Annotated[list, add_messages]
    current_step: str
