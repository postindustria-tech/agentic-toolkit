"""
Review and Edit Example

This example demonstrates how to pause the graph to allow humans to
review and edit content before proceeding.

Run this example:
    python examples/review-and-edit.py
"""

from typing import TypedDict
import uuid

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command


# Define the graph state
class State(TypedDict):
    """State schema for the review workflow."""
    topic: str
    draft_content: str
    final_content: str
    reviewed: bool


def generate_draft(state: State) -> State:
    """Simulate generating draft content."""
    print(f"\n📝 Generating draft content about: {state['topic']}")

    # Simulate AI-generated content
    draft = f"""
    Introduction to {state['topic']}

    {state['topic']} is an important concept in modern software development.
    This technology enables developers to build more efficient and scalable systems.

    Key Benefits:
    - Improved performance
    - Better developer experience
    - Enhanced maintainability

    Conclusion:
    {state['topic']} represents the future of software architecture.
    """.strip()

    print("✅ Draft generated!")
    return {"draft_content": draft}


def review_and_edit(state: State) -> State:
    """
    Pause for human review and editing.

    The human can review the draft and provide an edited version.
    """
    print("\n👁️ Review Stage")
    print("=" * 60)
    print(state["draft_content"])
    print("=" * 60)
    print("\n⏸️ Waiting for human review...")

    # Pause and request edited content
    edited_content = interrupt({
        "instruction": "Please review and edit this content",
        "draft": state["draft_content"],
        "topic": state["topic"],
        "guidelines": [
            "Fix any factual errors",
            "Improve clarity and tone",
            "Add specific examples if needed"
        ]
    })

    print("\n✏️ Content edited by human reviewer")
    return {
        "final_content": edited_content,
        "reviewed": True
    }


def publish_content(state: State) -> State:
    """Publish the reviewed content."""
    print("\n🚀 Publishing content...")
    print("=" * 60)
    print(state["final_content"])
    print("=" * 60)
    print("\n✅ Content published successfully!")
    return state


# Build the graph
def build_review_workflow():
    """Build the review and edit workflow graph."""
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("generate", generate_draft)
    builder.add_node("review", review_and_edit)
    builder.add_node("publish", publish_content)

    # Define edges
    builder.add_edge(START, "generate")
    builder.add_edge("generate", "review")
    builder.add_edge("review", "publish")
    builder.add_edge("publish", END)

    # Compile with checkpointer (required for interrupts)
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


def main():
    """Run the review and edit example."""
    graph = build_review_workflow()

    # Create a unique thread ID for this execution
    thread_id = f"review-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    print("=" * 60)
    print("REVIEW AND EDIT WORKFLOW EXAMPLE")
    print("=" * 60)

    # Initial run - will hit the interrupt at review stage
    print("\n[1] Initial execution - generating draft...")
    result = graph.invoke({
        "topic": "LangGraph Human-in-the-Loop",
        "draft_content": "",
        "final_content": "",
        "reviewed": False
    }, config=config)

    # Check if we hit an interrupt
    if "__interrupt__" in result:
        print(f"\n📋 Interrupt Info:")
        interrupt_info = result["__interrupt__"][0]
        print(f"   Instruction: {interrupt_info.value['instruction']}")
        print(f"   Topic: {interrupt_info.value['topic']}")

        # Simulate human editing
        print("\n[2] Resuming with edited content...")

        edited_version = """
        Introduction to LangGraph Human-in-the-Loop

        LangGraph's human-in-the-loop capabilities allow developers to build
        AI agents that pause for human feedback, approval, or intervention.

        Key Benefits:
        - **Increased Safety**: Human oversight for critical actions
        - **Better Quality**: Human review improves LLM outputs
        - **Flexibility**: Pause and resume workflows indefinitely

        Implementation:
        Use the interrupt() function to pause graph execution and the
        Command primitive to resume with human input.

        Conclusion:
        Human-in-the-loop is essential for production-ready AI agents that
        require reliability, accountability, and human judgment.
        """

        # Resume the graph with edited content
        final_result = graph.invoke(
            Command(resume=edited_version.strip()),
            config=config
        )

        print(f"\n🎯 Workflow completed!")
        print(f"   Reviewed: {final_result['reviewed']}")
    else:
        print("\n❗ No interrupt encountered (unexpected)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
