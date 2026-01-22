"""Webhook usage examples."""

import asyncio
import os
from langgraph_sdk import get_client


async def run_with_webhook(message: str, webhook_url: str):
    """Run graph with webhook notification on completion.

    Args:
        message: Message to process
        webhook_url: Webhook endpoint to call on completion
    """
    client = get_client(url=os.getenv("DEPLOYMENT_URL"))

    # Create thread
    thread = await client.threads.create()

    print(f"Starting run with webhook: {webhook_url}")

    # Run with webhook (non-blocking)
    run = await client.runs.create(
        thread["thread_id"],
        "agent",
        input={"messages": [{"role": "user", "content": message}], "current_step": "webhook_test"},
        webhook=webhook_url
    )

    print(f"Run started: {run['run_id']}")
    print(f"Status: {run['status']}")

    # Wait for completion
    await client.runs.join(thread["thread_id"], run["run_id"])

    print(f"Run completed - webhook should have been called")
    print(f"Check webhook server logs for payload")


async def cron_with_webhook(schedule: str, message: str, webhook_url: str):
    """Create cron job with webhook notification.

    Args:
        schedule: Cron expression
        message: Message for each execution
        webhook_url: Webhook endpoint
    """
    client = get_client(url=os.getenv("DEPLOYMENT_URL"))

    cron_job = await client.crons.create(
        "agent",
        schedule=schedule,
        input={"messages": [{"role": "user", "content": message}], "current_step": "cron_webhook"},
        webhook=webhook_url,
        on_run_completed="keep",  # Keep for webhook payload access
        metadata={"webhook_enabled": True}
    )

    print(f"Created cron with webhook: {cron_job['cron_id']}")
    print(f"Schedule: {schedule}")
    print(f"Webhook: {webhook_url}")
    print(f"Webhook will be called after each execution")


async def main():
    """Run webhook examples."""
    import argparse

    parser = argparse.ArgumentParser(description="Webhook Examples")
    parser.add_argument("--mode", choices=["run", "cron"], default="run",
                       help="Webhook mode")
    parser.add_argument("--message", default="Test webhook", help="Message to process")
    parser.add_argument("--webhook", default="http://localhost:8080/webhook",
                       help="Webhook URL")
    parser.add_argument("--schedule", default="*/5 * * * *",
                       help="Cron schedule (for cron mode)")

    args = parser.parse_args()

    if args.mode == "run":
        await run_with_webhook(args.message, args.webhook)
    elif args.mode == "cron":
        await cron_with_webhook(args.schedule, args.message, args.webhook)


if __name__ == "__main__":
    asyncio.run(main())
