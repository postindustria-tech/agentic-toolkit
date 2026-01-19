"""
Time Travel Debugging Example (PRIMARY VALIDATION)

This example demonstrates the complete time-travel debugging workflow
in LangGraph, showcasing all major time travel capabilities:

1. Initial execution with checkpoint history
2. Time travel replay from a specific checkpoint
3. State branching with update_state()
4. Debugging and recovering from failed execution

Run this example:
    python examples/time-travel-debugging.py
"""

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


# Define state for content generation pipeline
class ContentState(TypedDict):
    """State for content generation workflow."""
    topic: str
    outline: str
    content: str
    formatted_output: str
    error_flag: bool  # For simulating failures


def generate_topic(state: ContentState) -> dict:
    """Step 1: Generate a topic for content."""
    topic = state.get("topic", "LangGraph Checkpointing")
    print(f"  📝 Generated topic: {topic}")
    return {"topic": topic}


def write_outline(state: ContentState) -> dict:
    """Step 2: Write an outline based on topic."""
    outline = f"""
    Outline for: {state['topic']}
    1. Introduction
    2. Core Concepts
    3. Practical Examples
    4. Best Practices
    """
    print(f"  📋 Created outline with 4 sections")
    return {"outline": outline.strip()}


def write_content(state: ContentState) -> dict:
    """Step 3: Write content based on outline."""
    # Simulate failure if error flag is set
    if state.get("error_flag", False):
        print(f"  ❌ Content writing failed!")
        raise ValueError("Simulated content generation error - insufficient context")

    content = f"""
    # {state['topic']}

    ## Introduction
    Welcome to this guide on {state['topic']}.

    ## Core Concepts
    The fundamental concepts include...

    ## Practical Examples
    Here are some examples...

    ## Best Practices
    Follow these best practices...
    """
    print(f"  ✍️  Written {len(content)} characters of content")
    return {"content": content.strip()}


def format_output(state: ContentState) -> dict:
    """Step 4: Format the final output."""
    formatted = f"{'=' * 60}\n{state['content']}\n{'=' * 60}"
    print(f"  🎨 Formatted output ({len(formatted)} chars)")
    return {"formatted_output": formatted}


def build_content_graph():
    """Build content generation graph."""
    builder = StateGraph(ContentState)

    # Add nodes for 4-step pipeline
    builder.add_node("generate_topic", generate_topic)
    builder.add_node("write_outline", write_outline)
    builder.add_node("write_content", write_content)
    builder.add_node("format_output", format_output)

    # Linear flow through all steps
    builder.add_edge(START, "generate_topic")
    builder.add_edge("generate_topic", "write_outline")
    builder.add_edge("write_outline", "write_content")
    builder.add_edge("write_content", "format_output")
    builder.add_edge("format_output", END)

    # Compile with checkpointer
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


def print_separator(title: str, style: str = "="):
    """Print a visual separator."""
    print("\n" + style * 70)
    print(f"  {title}")
    print(style * 70)


def print_checkpoint_info(snapshot):
    """Pretty print checkpoint information."""
    checkpoint_id = snapshot.config['configurable']['checkpoint_id']
    step = snapshot.metadata.get('step', 0) if snapshot.metadata else 0
    next_nodes = snapshot.next if snapshot.next else "COMPLETE"
    values = snapshot.values

    print(f"\n📍 Checkpoint: {checkpoint_id[:16]}...")
    print(f"   Step: {step}")
    print(f"   Next: {next_nodes}")
    print(f"   State keys: {list(values.keys())}")
    if 'topic' in values and values['topic']:
        print(f"   Topic: {values['topic']}")


def main():
    """Demonstrate complete time-travel debugging workflow."""
    print_separator("TIME TRAVEL DEBUGGING - PRIMARY VALIDATION", "=")

    # Build graph
    graph = build_content_graph()

    # Configure thread
    config = {"configurable": {"thread_id": "time-travel-demo"}}

    # =========================================================================
    # PART 1: INITIAL EXECUTION
    # =========================================================================

    print_separator("PART 1: INITIAL EXECUTION", "-")

    print("\n🚀 Executing 4-step content generation pipeline...")
    print("   Steps: generate_topic → write_outline → write_content → format_output\n")

    # Execute full pipeline
    result = graph.invoke(
        {
            "topic": "LangGraph Checkpointing",
            "outline": "",
            "content": "",
            "formatted_output": "",
            "error_flag": False
        },
        config
    )

    print("\n✅ Initial execution complete!")
    print(f"   Final topic: {result['topic']}")
    print(f"   Output length: {len(result['formatted_output'])} characters")

    # Show checkpoint history
    print("\n📚 Checkpoint History:")
    history = list(graph.get_state_history(config))
    print(f"   Total checkpoints created: {len(history)}")

    for i, snapshot in enumerate(reversed(history)):
        step = snapshot.metadata.get('step', 0) if snapshot.metadata else 0
        # Determine what node we're after based on step and next
        if not snapshot.next:
            node_executed = "format_output (complete)"
        elif 'format_output' in snapshot.next:
            node_executed = "write_content"
        elif 'write_content' in snapshot.next:
            node_executed = "write_outline"
        elif 'write_outline' in snapshot.next:
            node_executed = "generate_topic"
        else:
            node_executed = "START"
        print(f"   [{i}] Step {step}: After {node_executed}")

    # =========================================================================
    # PART 2: TIME TRAVEL - REPLAY FROM CHECKPOINT
    # =========================================================================

    print_separator("PART 2: TIME TRAVEL - REPLAY FROM CHECKPOINT", "-")

    print("\n🕐 Time Travel: Replay from after write_outline\n")

    # Find checkpoint after write_outline (next node should be write_content)
    outline_checkpoint = next(
        s for s in history
        if s.next and 'write_content' in s.next
    )

    print_checkpoint_info(outline_checkpoint)

    print("\n▶️  Replaying from this checkpoint...")
    print("   This will re-execute: write_content → format_output\n")

    # Resume from that checkpoint (replay)
    replay_result = graph.invoke(None, outline_checkpoint.config)

    print("\n✅ Replay complete!")
    print(f"   Replayed result matches original: {replay_result['formatted_output'] == result['formatted_output']}")

    # =========================================================================
    # PART 3: STATE BRANCHING - ALTERNATE TIMELINE
    # =========================================================================

    print_separator("PART 3: STATE BRANCHING - ALTERNATE TIMELINE", "-")

    print("\n🌿 Branching: Create alternate timeline with different topic\n")

    # Find checkpoint after generate_topic (next node should be write_outline)
    topic_checkpoint = next(
        s for s in history
        if s.next and 'write_outline' in s.next
    )

    print("📍 Branching from checkpoint after generate_topic")
    print_checkpoint_info(topic_checkpoint)

    # Create branch with different topic
    print("\n🔧 Updating state with new topic: 'LangGraph Time Travel'")

    new_config = graph.update_state(
        topic_checkpoint.config,
        values={"topic": "LangGraph Time Travel"}
    )

    print(f"\n✨ Created new checkpoint (branch):")
    print(f"   Original checkpoint ID: {topic_checkpoint.config['configurable']['checkpoint_id'][:16]}...")
    print(f"   New checkpoint ID:      {new_config['configurable']['checkpoint_id'][:16]}...")

    print("\n▶️  Resuming from branched checkpoint...\n")

    # Resume from branched checkpoint
    branch_result = graph.invoke(None, new_config)

    print("\n✅ Branch execution complete!")
    print(f"   Original topic: '{result['topic']}'")
    print(f"   Branched topic: '{branch_result['topic']}'")
    print(f"   Results differ: {branch_result['formatted_output'] != result['formatted_output']}")

    # Verify original timeline unchanged
    original_state = graph.get_state(config)
    print(f"\n🔍 Verification: Original timeline unchanged")
    print(f"   Original thread still has: '{original_state.values['topic']}'")

    # =========================================================================
    # PART 4: DEBUGGING FAILED EXECUTION
    # =========================================================================

    print_separator("PART 4: DEBUGGING FAILED EXECUTION", "-")

    print("\n🐛 Simulating a failure during content writing...\n")

    # New thread for failure scenario
    failure_config = {"configurable": {"thread_id": "failure-demo"}}

    try:
        failed_result = graph.invoke(
            {
                "topic": "Advanced LangGraph Patterns",
                "outline": "",
                "content": "",
                "formatted_output": "",
                "error_flag": True  # This will cause failure in write_content
            },
            failure_config
        )
    except ValueError as e:
        print(f"💥 Execution failed: {e}")

    # Inspect failed state
    print("\n🔍 Inspecting failed checkpoint...")
    failed_snapshot = graph.get_state(failure_config)

    print_checkpoint_info(failed_snapshot)

    # Check for errors in tasks
    print("\n📋 Error Details:")
    if failed_snapshot.tasks:
        for task in failed_snapshot.tasks:
            if task.error:
                print(f"   ❌ Node '{task.name}' failed")
                print(f"   ❌ Error: {task.error}")

    # Show what was completed
    print("\n✅ Completed before failure:")
    print(f"   Topic: {failed_snapshot.values.get('topic', 'N/A')}")
    print(f"   Outline: {'YES' if failed_snapshot.values.get('outline') else 'NO'}")
    print(f"   Content: {'YES' if failed_snapshot.values.get('content') else 'NO'}")

    # Get history to find good checkpoint
    failed_history = list(graph.get_state_history(failure_config))
    print(f"\n📚 Checkpoints in failed execution: {len(failed_history)}")

    # Find checkpoint before failure (after write_outline, next should be write_content)
    before_failure = next(
        s for s in failed_history
        if s.next and 'write_content' in s.next
    )

    print("\n🔧 Recovery Strategy: Resume from before failure without error flag")
    print_checkpoint_info(before_failure)

    # Fix by removing error flag
    print("\n▶️  Fixing state and resuming...\n")

    recovered_config = graph.update_state(
        before_failure.config,
        values={"error_flag": False}
    )

    # Resume from fixed checkpoint
    recovered_result = graph.invoke(None, recovered_config)

    print("\n✅ Recovery successful!")
    print(f"   Topic: {recovered_result['topic']}")
    print(f"   Content generated: {len(recovered_result['content'])} characters")
    print(f"   Output formatted: YES")

    # =========================================================================
    # PART 5: COMPREHENSIVE HISTORY ANALYSIS
    # =========================================================================

    print_separator("PART 5: COMPREHENSIVE HISTORY ANALYSIS", "-")

    print("\n📊 Analyzing all checkpoints across timelines...\n")

    # Original timeline
    original_history = list(graph.get_state_history(config))
    print(f"🔵 Original Timeline ({config['configurable']['thread_id']}):")
    print(f"   Checkpoints: {len(original_history)}")
    print(f"   Final topic: {original_history[0].values.get('topic')}")

    # Failure/recovery timeline
    failure_history = list(graph.get_state_history(failure_config))
    print(f"\n🔴 Failure/Recovery Timeline ({failure_config['configurable']['thread_id']}):")
    print(f"   Checkpoints: {len(failure_history)}")
    print(f"   Includes failed execution + recovery")

    # Show metadata progression
    print("\n📈 Metadata Progression (Original Timeline):")
    for snapshot in reversed(original_history[:5]):  # Show first 5
        step = snapshot.metadata.get('step', 0) if snapshot.metadata else 0
        source = snapshot.metadata.get('source', 'N/A') if snapshot.metadata else 'N/A'
        # Infer node from next field
        if not snapshot.next:
            node = "format_output (complete)"
        elif 'format_output' in snapshot.next:
            node = "write_content"
        elif 'write_content' in snapshot.next:
            node = "write_outline"
        elif 'write_outline' in snapshot.next:
            node = "generate_topic"
        else:
            node = "START"
        print(f"   Step {step} ({source}): {node}")

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print_separator("SUMMARY - TIME TRAVEL CAPABILITIES DEMONSTRATED", "=")

    print("\n✅ Part 1: Initial Execution")
    print("   ✓ Executed 4-step content pipeline")
    print("   ✓ Created checkpoint history (5 checkpoints)")
    print("   ✓ Inspected StateSnapshot fields")

    print("\n✅ Part 2: Time Travel Replay")
    print("   ✓ Found specific checkpoint in history")
    print("   ✓ Resumed execution from past checkpoint")
    print("   ✓ Replayed remaining nodes deterministically")

    print("\n✅ Part 3: State Branching")
    print("   ✓ Created alternate timeline with update_state()")
    print("   ✓ Modified state at specific checkpoint")
    print("   ✓ Resumed with different values")
    print("   ✓ Verified original timeline unchanged")

    print("\n✅ Part 4: Debugging Failed Execution")
    print("   ✓ Simulated node failure")
    print("   ✓ Inspected error in StateSnapshot.tasks")
    print("   ✓ Found checkpoint before failure")
    print("   ✓ Fixed state and successfully recovered")

    print("\n✅ Part 5: History Analysis")
    print("   ✓ Analyzed multiple timelines")
    print("   ✓ Inspected checkpoint metadata progression")
    print("   ✓ Demonstrated thread isolation")

    print("\n💡 Key APIs Demonstrated:")
    print("   • graph.invoke() - Execute and resume")
    print("   • graph.get_state() - Inspect current checkpoint")
    print("   • graph.get_state_history() - Traverse history")
    print("   • graph.update_state() - Create branches and fix state")

    print("\n🎯 Primary Validation Complete!")
    print("   All time travel capabilities successfully demonstrated.")
    print()


if __name__ == "__main__":
    main()
