"""Cron job creation and management examples."""

import asyncio
import os
from langgraph_sdk import get_client


async def create_stateless_cron(schedule: str, message: str):
    """Create stateless cron job (new thread per execution).

    Args:
        schedule: Cron expression (e.g., "0 9 * * *")
        message: Message to send on each execution
    """
    client = get_client(url=os.getenv("DEPLOYMENT_URL"))

    cron_job = await client.crons.create(
        "agent",
        schedule=schedule,
        input={"messages": [{"role": "user", "content": message}], "current_step": "cron_started"},
        on_run_completed="delete",  # Auto-delete thread after run
        metadata={"type": "stateless", "purpose": "daily_summary"}
    )

    print(f"Created stateless cron job: {cron_job['cron_id']}")
    print(f"Schedule: {schedule}")
    print(f"Thread cleanup: auto-delete")


async def create_stateful_cron(schedule: str, message: str):
    """Create thread-based cron job (stateful, context accumulates).

    Args:
        schedule: Cron expression (e.g., "*/30 * * * *")
        message: Message to send on each execution
    """
    client = get_client(url=os.getenv("DEPLOYMENT_URL"))

    # Create persistent thread
    thread = await client.threads.create()

    # Create cron on specific thread
    cron_job = await client.crons.create_for_thread(
        thread["thread_id"],
        "agent",
        schedule=schedule,
        input={"messages": [{"role": "user", "content": message}], "current_step": "monitoring"},
        metadata={"type": "stateful", "purpose": "continuous_monitoring"}
    )

    print(f"Created stateful cron job: {cron_job['cron_id']}")
    print(f"Thread: {thread['thread_id']}")
    print(f"Schedule: {schedule}")
    print(f"Context: accumulates over time")


async def list_crons():
    """List all cron jobs."""
    client = get_client(url=os.getenv("DEPLOYMENT_URL"))

    cron_jobs = await client.crons.list()

    print(f"Total cron jobs: {len(cron_jobs)}")
    for cron in cron_jobs:
        print(f"  - {cron['cron_id']}: {cron['schedule']} ({cron.get('metadata', {}).get('purpose', 'N/A')})")


async def delete_cron(cron_id: str):
    """Delete a cron job.

    Args:
        cron_id: Cron job ID to delete
    """
    client = get_client(url=os.getenv("DEPLOYMENT_URL"))

    await client.crons.delete(cron_id)
    print(f"Deleted cron job: {cron_id}")


async def main():
    """Run cron management examples."""
    import argparse

    parser = argparse.ArgumentParser(description="Cron Job Examples")
    parser.add_argument("--mode", choices=["create", "list", "delete"], default="create",
                       help="Operation mode")
    parser.add_argument("--schedule", default="0 9 * * *", help="Cron schedule expression")
    parser.add_argument("--message", default="Automated task", help="Message for cron execution")
    parser.add_argument("--stateful", action="store_true", help="Create stateful (thread-based) cron")
    parser.add_argument("--cron-id", help="Cron ID (for delete mode)")

    args = parser.parse_args()

    if args.mode == "create":
        if args.stateful:
            await create_stateful_cron(args.schedule, args.message)
        else:
            await create_stateless_cron(args.schedule, args.message)
    elif args.mode == "list":
        await list_crons()
    elif args.mode == "delete":
        if not args.cron_id:
            print("Error: --cron-id required for delete mode")
            return
        await delete_cron(args.cron_id)


if __name__ == "__main__":
    asyncio.run(main())
