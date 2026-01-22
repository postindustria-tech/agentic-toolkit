"""RemoteGraph client usage examples."""

import asyncio
import os
from langgraph.pregel.remote import RemoteGraph
from langgraph_sdk import get_client


async def create_assistants():
    """Create assistants with different configurations."""
    client = get_client(url=os.getenv("DEPLOYMENT_URL"))

    # Sonnet assistant (high quality)
    sonnet = await client.assistants.create(
        "agent",
        context={
            "model_name": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 2048
        },
        name="Sonnet Assistant",
        metadata={"variant": "quality", "use_case": "complex_tasks"}
    )
    print(f"Created Sonnet Assistant: {sonnet['assistant_id']}")

    # Haiku assistant (fast)
    haiku = await client.assistants.create(
        "agent",
        context={
            "model_name": "claude-3-5-haiku-20241022",
            "temperature": 0.5,
            "max_tokens": 1024
        },
        name="Haiku Assistant",
        metadata={"variant": "speed", "use_case": "simple_tasks"}
    )
    print(f"Created Haiku Assistant: {haiku['assistant_id']}")


async def invoke_example(message: str):
    """Single invocation with RemoteGraph.

    Args:
        message: User message to process
    """
    url = os.getenv("DEPLOYMENT_URL")
    remote_graph = RemoteGraph("agent", url=url)

    # Invoke (stateless)
    result = await remote_graph.ainvoke({
        "messages": [{"role": "user", "content": message}],
        "current_step": "started"
    })

    print(f"Response: {result['messages'][-1]['content']}")


async def stream_example(message: str, thread_id: str = "user-123"):
    """Streaming with thread persistence.

    Args:
        message: User message to process
        thread_id: Thread ID for conversation continuity
    """
    url = os.getenv("DEPLOYMENT_URL")
    remote_graph = RemoteGraph("agent", url=url)

    # Thread configuration for persistence
    config = {"configurable": {"thread_id": thread_id}}

    # Stream with state persistence
    print(f"Streaming response (thread: {thread_id})...")
    async for chunk in remote_graph.astream(
        {
            "messages": [{"role": "user", "content": message}],
            "current_step": "streaming"
        },
        config=config,
        stream_mode="updates"
    ):
        print(chunk)


async def get_state_example(thread_id: str = "user-123"):
    """Get thread state.

    Args:
        thread_id: Thread ID to inspect
    """
    url = os.getenv("DEPLOYMENT_URL")
    remote_graph = RemoteGraph("agent", url=url)

    config = {"configurable": {"thread_id": thread_id}}
    state = await remote_graph.aget_state(config)

    print(f"Thread state: {state}")
    print(f"Messages: {len(state.values['messages'])}")


async def update_state_example(thread_id: str = "user-123"):
    """Update thread state manually.

    Args:
        thread_id: Thread ID to update
    """
    url = os.getenv("DEPLOYMENT_URL")
    remote_graph = RemoteGraph("agent", url=url)

    config = {"configurable": {"thread_id": thread_id}}

    # Add a message directly to state
    await remote_graph.aupdate_state(
        config,
        values={"messages": [{"role": "assistant", "content": "State updated!"}]}
    )
    print(f"Updated state for thread: {thread_id}")


async def main():
    """Run examples based on command line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="RemoteGraph Client Examples")
    parser.add_argument("--mode", choices=["create-assistants", "invoke", "stream", "get-state", "update-state"],
                       required=True, help="Example mode to run")
    parser.add_argument("--message", help="Message to send (for invoke/stream)")
    parser.add_argument("--thread-id", default="user-123", help="Thread ID (for stateful operations)")

    args = parser.parse_args()

    if args.mode == "create-assistants":
        await create_assistants()
    elif args.mode == "invoke":
        if not args.message:
            print("Error: --message required for invoke mode")
            return
        await invoke_example(args.message)
    elif args.mode == "stream":
        if not args.message:
            print("Error: --message required for stream mode")
            return
        await stream_example(args.message, args.thread_id)
    elif args.mode == "get-state":
        await get_state_example(args.thread_id)
    elif args.mode == "update-state":
        await update_state_example(args.thread_id)


if __name__ == "__main__":
    asyncio.run(main())
