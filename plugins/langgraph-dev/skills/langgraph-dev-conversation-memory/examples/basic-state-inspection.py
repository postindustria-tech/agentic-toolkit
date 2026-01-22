"""
Basic State Inspection Example

This example demonstrates how to use get_state() to inspect StateSnapshot
and understand all the fields available in a checkpoint.

Run this example:
    python examples/basic-state-inspection.py
"""

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


# Define state schema
class ProcessState(TypedDict):
    """State for a simple data processing pipeline."""
    input_data: str
    step1_result: str
    step2_result: str
    final_output: str


def step1_validate(state: ProcessState) -> dict:
    """Step 1: Validate and clean input data."""
    cleaned = state["input_data"].strip().lower()
    return {"step1_result": f"validated:{cleaned}"}


def step2_transform(state: ProcessState) -> dict:
    """Step 2: Transform the validated data."""
    transformed = state["step1_result"].replace(":", "_").upper()
    return {"step2_result": transformed}


def step3_finalize(state: ProcessState) -> dict:
    """Step 3: Finalize the output."""
    final = f"FINAL[{state['step2_result']}]"
    return {"final_output": final}


def build_graph():
    """Build a simple 3-step processing graph."""
    builder = StateGraph(ProcessState)

    # Add nodes
    builder.add_node("validate", step1_validate)
    builder.add_node("transform", step2_transform)
    builder.add_node("finalize", step3_finalize)

    # Add edges (linear flow)
    builder.add_edge(START, "validate")
    builder.add_edge("validate", "transform")
    builder.add_edge("transform", "finalize")
    builder.add_edge("finalize", END)

    # Compile with checkpointer
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


def print_separator(title: str):
    """Print a visual separator."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    """Demonstrate state inspection with get_state()."""
    print_separator("BASIC STATE INSPECTION EXAMPLE")

    # Build graph
    graph = build_graph()

    # Configure thread
    config = {"configurable": {"thread_id": "inspection-demo"}}

    print("\n📊 Executing graph with input: 'Hello World'")
    print("-" * 70)

    # Execute graph
    result = graph.invoke(
        {"input_data": "  Hello World  "},  # Intentional whitespace
        config
    )

    print(f"✅ Execution complete!")
    print(f"   Final output: {result['final_output']}")

    # =========================================================================
    # INSPECT STATE SNAPSHOT
    # =========================================================================

    print_separator("STATE SNAPSHOT INSPECTION")

    # Get current state
    snapshot = graph.get_state(config)

    # 1. VALUES - Current state values
    print("\n🔷 1. VALUES (Current State)")
    print("-" * 70)
    print(f"Type: {type(snapshot.values)}")
    print(f"Content:")
    for key, value in snapshot.values.items():
        print(f"  {key:20} = {value}")

    # 2. NEXT - Nodes to execute next
    print("\n🔷 2. NEXT (Next Nodes to Execute)")
    print("-" * 70)
    print(f"Type: {type(snapshot.next)}")
    print(f"Content: {snapshot.next}")
    if snapshot.next:
        print(f"  → Graph will execute: {', '.join(snapshot.next)}")
    else:
        print(f"  → Graph execution is COMPLETE (empty tuple)")

    # 3. CONFIG - Configuration with identifiers
    print("\n🔷 3. CONFIG (Checkpoint Configuration)")
    print("-" * 70)
    print(f"Type: {type(snapshot.config)}")
    config_info = snapshot.config.get('configurable', {})
    print(f"Thread ID:     {config_info.get('thread_id')}")
    print(f"Checkpoint ID: {config_info.get('checkpoint_id')}")
    print(f"Checkpoint NS: {config_info.get('checkpoint_ns', '(empty)')}")

    # 4. METADATA - Execution metadata
    print("\n🔷 4. METADATA (Checkpoint Metadata)")
    print("-" * 70)
    print(f"Type: {type(snapshot.metadata)}")
    if snapshot.metadata:
        print(f"Step:   {snapshot.metadata.get('step')} (execution counter)")
        print(f"Source: {snapshot.metadata.get('source')} ('input' or 'loop')")
        print(f"Writes: {snapshot.metadata.get('writes', {})} (node outputs)")
    else:
        print("  (No metadata)")

    # 5. CREATED_AT - Timestamp
    print("\n🔷 5. CREATED_AT (Checkpoint Timestamp)")
    print("-" * 70)
    print(f"Type: {type(snapshot.created_at)}")
    print(f"Value: {snapshot.created_at}")
    print(f"  → ISO 8601 format timestamp")

    # 6. PARENT_CONFIG - Previous checkpoint
    print("\n🔷 6. PARENT_CONFIG (Previous Checkpoint)")
    print("-" * 70)
    print(f"Type: {type(snapshot.parent_config)}")
    if snapshot.parent_config:
        parent_checkpoint_id = snapshot.parent_config['configurable']['checkpoint_id']
        print(f"Parent Checkpoint ID: {parent_checkpoint_id}")
        print(f"  → Links to previous checkpoint in history chain")
    else:
        print(f"Value: None")
        print(f"  → This is the initial checkpoint (no parent)")

    # 7. TASKS - Pending or failed tasks
    print("\n🔷 7. TASKS (Pending/Failed Tasks)")
    print("-" * 70)
    print(f"Type: {type(snapshot.tasks)}")
    print(f"Content: {snapshot.tasks}")
    if snapshot.tasks:
        print(f"  → Contains {len(snapshot.tasks)} task(s)")
        for task in snapshot.tasks:
            print(f"     Task: {task.name}")
            if task.error:
                print(f"     Error: {task.error}")
    else:
        print(f"  → No pending tasks (empty tuple)")

    # 8. INTERRUPTS - Human-in-the-loop interrupts
    print("\n🔷 8. INTERRUPTS (Pending Interrupts)")
    print("-" * 70)
    print(f"Type: {type(snapshot.interrupts)}")
    print(f"Content: {snapshot.interrupts}")
    if snapshot.interrupts:
        print(f"  → Contains {len(snapshot.interrupts)} interrupt(s)")
        for interrupt in snapshot.interrupts:
            print(f"     Value: {interrupt.value}")
    else:
        print(f"  → No interrupts (empty tuple)")

    # =========================================================================
    # PRACTICAL USE CASES
    # =========================================================================

    print_separator("PRACTICAL USE CASES")

    # Use Case 1: Check if execution is complete
    print("\n📌 Use Case 1: Check if graph execution is complete")
    if not snapshot.next:
        print("✅ Execution is complete (next is empty tuple)")
    else:
        print(f"⏳ Execution in progress, next nodes: {snapshot.next}")

    # Use Case 2: Get specific state value
    print("\n📌 Use Case 2: Access specific state values")
    final_output = snapshot.values.get("final_output")
    print(f"Final output from state: {final_output}")

    # Use Case 3: Check execution progress
    print("\n📌 Use Case 3: Check execution progress")
    step_number = snapshot.metadata.get("step", 0) if snapshot.metadata else 0
    print(f"Current step: {step_number}")
    print(f"Last node executed: {list(snapshot.metadata.get('writes', {}).keys())}")

    # Use Case 4: Get checkpoint ID for later resumption
    print("\n📌 Use Case 4: Save checkpoint ID for resumption")
    checkpoint_id = snapshot.config['configurable']['checkpoint_id']
    print(f"Checkpoint ID: {checkpoint_id}")
    print(f"To resume from this exact checkpoint:")
    print(f"  config = {{")
    print(f"      'configurable': {{")
    print(f"          'thread_id': '{config_info.get('thread_id')}',")
    print(f"          'checkpoint_id': '{checkpoint_id}'")
    print(f"      }}")
    print(f"  }}")
    print(f"  graph.invoke(None, config)")

    print_separator("EXAMPLE COMPLETE")
    print("✅ Successfully demonstrated StateSnapshot inspection!")
    print("   All 8 fields explained and demonstrated.")
    print()


if __name__ == "__main__":
    main()
