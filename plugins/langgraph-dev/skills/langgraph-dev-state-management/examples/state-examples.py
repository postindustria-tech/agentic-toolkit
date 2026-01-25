"""
State Management Examples for LangGraph

Examples demonstrating common state patterns with correct imports and types.
"""

from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import operator

# ============================================================================
# Example 1: Basic State with add_messages
# ============================================================================

class BasicState(TypedDict):
    """Simple state for conversational workflow using add_messages."""
    messages: Annotated[list[BaseMessage], add_messages]
    next_step: str


def greet(state: BasicState) -> dict:
    """Node that adds greeting message."""
    return {
        "messages": [AIMessage(content="Hello! What's your name?")],
        "next_step": "get_name"
    }


def get_name(state: BasicState) -> dict:
    """Node that processes user's name."""
    # Get the last message content safely
    last_message = state["messages"][-1]
    name = last_message.content if hasattr(last_message, 'content') else str(last_message)
    return {
        "messages": [AIMessage(content=f"Nice to meet you, {name}!")],
        "next_step": "end"
    }


# ============================================================================
# Example 2: Append-Only Messages with add_messages
# ============================================================================

class AppendOnlyState(TypedDict):
    """State with append-only message list using add_messages."""
    messages: Annotated[list[BaseMessage], add_messages]
    current_step: str


def add_message_1(state: AppendOnlyState) -> dict:
    """First node adds a message."""
    return {"messages": [HumanMessage(content="First message")]}


def add_message_2(state: AppendOnlyState) -> dict:
    """Second node appends another message."""
    return {"messages": [AIMessage(content="Second message")]}

# Result: state["messages"] contains both messages (appended, not replaced)


# ============================================================================
# Example 3: Task List Execution with add_messages
# ============================================================================

class TaskState(TypedDict):
    """State for sequential task execution."""
    messages: Annotated[list[BaseMessage], add_messages]
    current_step: str
    task_list: list[str]
    error_count: int


def break_down_task(state: TaskState) -> dict:
    """Break user request into subtasks."""
    # Simulate task breakdown
    subtasks = [
        "Step 1: Analyze requirements",
        "Step 2: Design solution",
        "Step 3: Implement code"
    ]
    return {
        "task_list": subtasks,
        "messages": [AIMessage(content=f"I've broken down your task into {len(subtasks)} steps")],
        "current_step": "execute_subtask"
    }


def execute_subtask(state: TaskState) -> dict:
    """Execute one subtask and update state."""
    if not state["task_list"]:
        return {"current_step": "summarize"}

    current_task = state["task_list"][0]
    remaining_tasks = state["task_list"][1:]

    # Execute task (simulated)
    next_step = "execute_subtask" if remaining_tasks else "summarize"

    return {
        "messages": [AIMessage(content=f"Completed: {current_task}")],
        "task_list": remaining_tasks,
        "current_step": next_step
    }


# ============================================================================
# Example 4: Error Handling State
# ============================================================================

class ErrorTrackingState(TypedDict):
    """State with error counting and recovery."""
    messages: Annotated[list[BaseMessage], add_messages]
    current_step: str
    error_count: int


def handle_error(state: ErrorTrackingState) -> dict:
    """Handle errors with retry limit."""
    error_count = state["error_count"] + 1

    if error_count > 3:
        return {
            "messages": [AIMessage(content="Let's start over.")],
            "error_count": 0,
            "current_step": "restart"
        }
    else:
        return {
            "messages": [AIMessage(content="Could you please rephrase?")],
            "error_count": error_count,
            "current_step": "retry"
        }


# ============================================================================
# Example 5: Parallel Execution with Reducers (operator.add)
# ============================================================================

class ParallelState(TypedDict):
    """State for parallel node execution."""
    results: Annotated[list, operator.add]
    input_data: str


def parallel_branch_1(state: ParallelState) -> dict:
    """First parallel branch."""
    return {"results": [1, 2, 3]}


def parallel_branch_2(state: ParallelState) -> dict:
    """Second parallel branch."""
    return {"results": [4, 5, 6]}


def parallel_branch_3(state: ParallelState) -> dict:
    """Third parallel branch."""
    return {"results": [7, 8, 9]}

# When all three execute in parallel, state["results"] = [1,2,3,4,5,6,7,8,9]


# ============================================================================
# Example 6: Custom Reducer
# ============================================================================

def deduplicate_merge(existing: list, new: list) -> list:
    """Custom reducer that merges while removing duplicates."""
    seen = set(existing)
    return existing + [x for x in new if x not in seen]


class DeduplicatedState(TypedDict):
    """State with custom deduplication reducer."""
    unique_items: Annotated[list, deduplicate_merge]


def add_items_1(state: DeduplicatedState) -> dict:
    return {"unique_items": [1, 2, 3]}


def add_items_2(state: DeduplicatedState) -> dict:
    return {"unique_items": [2, 3, 4]}  # 2 and 3 are duplicates

# Result: state["unique_items"] = [1, 2, 3, 4] (duplicates removed)


# ============================================================================
# Example 7: Confidence-Based Routing
# ============================================================================

class RoutingState(TypedDict):
    """State for conditional routing based on confidence."""
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str
    confidence: float


def classify_intent(state: RoutingState) -> dict:
    """Classify user intent with confidence score."""
    # Simulate classification
    return {
        "intent": "query",
        "confidence": 0.95
    }


def should_continue(state: RoutingState) -> str:
    """Conditional routing based on confidence."""
    if state["confidence"] > 0.8:
        return "high_confidence_path"
    return "low_confidence_path"


# ============================================================================
# Example 8: State Initialization Helper
# ============================================================================

def create_initial_state(user_input: str) -> TaskState:
    """Factory function for consistent state initialization."""
    return {
        "messages": [HumanMessage(content=user_input)],
        "current_step": "start",
        "task_list": [],
        "error_count": 0
    }


# ============================================================================
# Example 9: State Validation
# ============================================================================

def validate_state(state: TaskState) -> bool:
    """Validate state integrity before processing."""
    if not isinstance(state.get("messages"), list):
        print("Error: messages must be a list")
        return False

    if not isinstance(state.get("task_list"), list):
        print("Error: task_list must be a list")
        return False

    error_count = state.get("error_count", 0)
    if error_count < 0:
        print("Error: error_count cannot be negative")
        return False

    return True


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    print("State Management Examples")
    print("=" * 60)

    # Example 1: Basic state
    print("\n1. Basic State:")
    basic_state: BasicState = {"messages": [], "next_step": "greet"}
    result = greet(basic_state)
    print(f"   After greet: {result}")

    # Example 2: Task state initialization
    print("\n2. Task State Initialization:")
    task_state = create_initial_state("Build a chatbot")
    print(f"   Initial state messages: {len(task_state['messages'])} message(s)")
    if validate_state(task_state):
        print("   State validation passed")

    # Example 3: Error handling
    print("\n3. Error Handling:")
    error_state: ErrorTrackingState = {
        "messages": [],
        "current_step": "process",
        "error_count": 2
    }
    error_result = handle_error(error_state)
    print(f"   After error (count=2): error_count={error_result['error_count']}")

    error_state["error_count"] = 4
    error_result = handle_error(error_state)
    print(f"   After error (count=4): current_step={error_result['current_step']}")

    # Example 4: Custom reducer
    print("\n4. Custom Reducer (Deduplication):")
    existing = [1, 2, 3]
    new = [2, 3, 4, 5]
    merged = deduplicate_merge(existing, new)
    print(f"   Merged: {existing} + {new} = {merged}")

    print("\n" + "=" * 60)
    print("All examples use langchain_core.messages and langgraph.graph imports")
