"""Simple webhook server for testing."""

from fastapi import FastAPI, Request
import uvicorn
import json

app = FastAPI(title="Webhook Test Server")


@app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming webhook from LangGraph Platform.

    Payload format:
    {
        "run_id": "...",
        "thread_id": "...",
        "assistant_id": "...",
        "status": "success" | "error" | "cancelled",
        "created_at": "...",
        "kwargs": {...},
        "output": {...}
    }
    """
    payload = await request.json()

    print("\n" + "="*80)
    print("WEBHOOK RECEIVED")
    print("="*80)
    print(f"Run ID: {payload.get('run_id')}")
    print(f"Thread ID: {payload.get('thread_id')}")
    print(f"Status: {payload.get('status')}")
    print(f"Created: {payload.get('created_at')}")

    # Extract output
    output = payload.get("output", {})
    if "messages" in output:
        last_message = output["messages"][-1] if output["messages"] else None
        if last_message:
            print(f"\nLast Message:")
            print(f"  Role: {last_message.get('role')}")
            print(f"  Content: {last_message.get('content', '')[:200]}")

    print("\nFull Payload:")
    print(json.dumps(payload, indent=2))
    print("="*80 + "\n")

    return {"status": "received", "run_id": payload.get("run_id")}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    print("Starting webhook server on http://localhost:8080")
    print("Webhook endpoint: http://localhost:8080/webhook")
    print("\nUse this URL in your webhook examples:")
    print("  python webhook_example.py --webhook='http://localhost:8080/webhook'")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(app, host="0.0.0.0", port=8080)
