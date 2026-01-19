# Error Handling and Resilience in Multi-Agent Systems

This reference provides advanced patterns for building resilient multi-agent supervisors.

## Contents

1. [Agent-Level Error Handling](#agent-level-error-handling)
2. [Supervisor-Level Error Handling](#supervisor-level-error-handling)
3. [Circuit Breaker Pattern](#circuit-breaker-pattern)
4. [Retry Strategies](#retry-strategies)
5. [Graceful Degradation](#graceful-degradation)
6. [Error Propagation](#error-propagation)

---

## Agent-Level Error Handling

### Pattern: Try-Except with Error State

**Purpose**: Capture agent failures without crashing workflow.

```python
from typing import TypedDict, List, Optional
from langchain_core.messages import AIMessage
import logging

logger = logging.getLogger(__name__)

class ResilientState(TypedDict):
    messages: List
    error: Optional[str]
    failed_agents: List[str]

def resilient_agent(state: ResilientState) -> dict:
    """
    Agent with comprehensive error handling.

    Catches all exceptions and returns error state instead of crashing.
    """
    try:
        # Simulate agent work (could be LLM call, API call, etc.)
        result = perform_agent_task(state)

        logger.info("Agent completed successfully")
        return {
            "messages": [AIMessage(content=result, name="agent")],
            "error": None
        }

    except ValueError as e:
        # Handle specific error types differently
        logger.error(f"Validation error in agent: {e}")
        return {
            "error": f"Validation failed: {str(e)}",
            "failed_agents": state.get("failed_agents", []) + ["agent"]
        }

    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error in agent: {e}", exc_info=True)
        return {
            "error": f"Agent failed: {str(e)}",
            "failed_agents": state.get("failed_agents", []) + ["agent"]
        }

def perform_agent_task(state):
    """Placeholder for actual agent logic."""
    # This is where LLM calls, API requests, etc. would happen
    return "Task completed"
```

**Key Points**:
- Never let exceptions propagate out of agent nodes
- Log errors with context for debugging
- Return error information in state
- Track which agents failed for reporting

---

## Supervisor-Level Error Handling

### Pattern: Supervisor with Fallback Routing

**Purpose**: Supervisor handles agent failures by routing to fallback agents or recovery flows.

```python
from typing import Literal

AgentRoute = Literal["primary", "fallback", "error_handler", "FINISH"]

def supervisor_with_fallback(state: ResilientState) -> dict:
    """
    Supervisor that routes to fallback agent on primary failure.

    Decision logic:
    - No error → route to primary agent
    - Error from primary → route to fallback
    - Error from fallback → route to error handler
    - Too many failures → FINISH
    """
    error = state.get("error")
    failed_agents = state.get("failed_agents", [])

    # Too many failures → give up
    if len(failed_agents) >= 3:
        logger.warning("Too many agent failures, ending workflow")
        return {"next_agent": "error_handler"}

    # Error handling routing
    if error:
        if "primary" in failed_agents and "fallback" not in failed_agents:
            logger.info("Primary failed, trying fallback agent")
            return {"next_agent": "fallback"}
        else:
            logger.error("Both primary and fallback failed")
            return {"next_agent": "error_handler"}

    # No error → normal routing
    return {"next_agent": "primary"}

def route_with_fallback(state: ResilientState) -> AgentRoute:
    """Router function for supervisor decisions."""
    next_agent = state.get("next_agent", "primary")

    valid_routes = ("primary", "fallback", "error_handler", "FINISH")
    if next_agent not in valid_routes:
        logger.warning(f"Invalid route '{next_agent}', defaulting to error_handler")
        return "error_handler"

    return next_agent  # type: ignore
```

**Key Points**:
- Supervisor monitors error state
- Routes to fallback agents on failure
- Limits retry attempts to prevent infinite loops
- Error handler provides final cleanup

---

## Circuit Breaker Pattern

**Purpose**: Prevent repeated calls to failing agents, giving them time to recover.

```python
from typing import Dict
from datetime import datetime, timedelta

class CircuitBreaker:
    """
    Circuit breaker for agent calls.

    States:
    - CLOSED: Normal operation, calls allowed
    - OPEN: Too many failures, calls blocked
    - HALF_OPEN: Testing if agent recovered
    """

    def __init__(self, failure_threshold: int = 3, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout)
        self.failure_count: Dict[str, int] = {}
        self.last_failure: Dict[str, datetime] = {}
        self.state: Dict[str, str] = {}  # "CLOSED", "OPEN", "HALF_OPEN"

    def call_allowed(self, agent_name: str) -> bool:
        """Check if calling this agent is allowed."""
        state = self.state.get(agent_name, "CLOSED")

        if state == "CLOSED":
            return True

        if state == "OPEN":
            # Check if timeout expired → try half-open
            last_fail = self.last_failure.get(agent_name)
            if last_fail and datetime.now() - last_fail > self.timeout:
                self.state[agent_name] = "HALF_OPEN"
                return True
            return False  # Still open, block call

        if state == "HALF_OPEN":
            return True  # Allow test call

        return False

    def record_success(self, agent_name: str):
        """Record successful call, reset circuit."""
        self.failure_count[agent_name] = 0
        self.state[agent_name] = "CLOSED"

    def record_failure(self, agent_name: str):
        """Record failed call, potentially open circuit."""
        self.failure_count[agent_name] = self.failure_count.get(agent_name, 0) + 1
        self.last_failure[agent_name] = datetime.now()

        if self.failure_count[agent_name] >= self.failure_threshold:
            self.state[agent_name] = "OPEN"
            logger.warning(f"Circuit breaker OPEN for {agent_name}")

# Usage in supervisor
circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=60)

def supervisor_with_circuit_breaker(state: ResilientState) -> dict:
    """Supervisor that uses circuit breaker."""
    # Check if primary agent is available
    if not circuit_breaker.call_allowed("primary_agent"):
        logger.warning("Circuit breaker blocking primary_agent, using fallback")
        return {"next_agent": "fallback"}

    return {"next_agent": "primary"}

def primary_agent_with_breaker(state: ResilientState) -> dict:
    """Agent that reports to circuit breaker."""
    try:
        result = perform_agent_task(state)
        circuit_breaker.record_success("primary_agent")
        return {"messages": [AIMessage(content=result)], "error": None}
    except Exception as e:
        circuit_breaker.record_failure("primary_agent")
        return {"error": str(e)}
```

**Key Points**:
- Prevents cascading failures
- Gives failing services time to recover
- Automatic retry after timeout
- Tracks failure counts per agent

---

## Retry Strategies

### Pattern: Exponential Backoff

**Purpose**: Retry failed operations with increasing delays.

```python
import time
from typing import Callable, Any

def exponential_backoff_retry(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Any:
    """
    Retry function with exponential backoff.

    Delays: 1s, 2s, 4s, 8s, ...
    """
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed, raise
                logger.error(f"All {max_retries} retry attempts failed")
                raise

            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= backoff_factor

    raise RuntimeError("Retry logic error")  # Should never reach here

# Usage in agent
def agent_with_retry(state: ResilientState) -> dict:
    """Agent that retries with exponential backoff."""
    try:
        def agent_work():
            # This could be an API call, LLM invocation, etc.
            return llm.invoke(state["messages"])

        result = exponential_backoff_retry(
            agent_work,
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0
        )

        return {"messages": [result], "error": None}

    except Exception as e:
        logger.error(f"Agent failed after retries: {e}")
        return {"error": f"Failed after retries: {str(e)}"}
```

**Alternative: Built-in Tenacity**

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def agent_with_tenacity(state: ResilientState) -> dict:
    """Agent using tenacity library for retries."""
    result = llm.invoke(state["messages"])  # Automatically retried
    return {"messages": [result]}
```

**Key Points**:
- Prevents overwhelming failing services
- Increases success rate for transient failures
- Use for network calls, external APIs, LLM calls
- Consider jitter to avoid thundering herd

---

## Graceful Degradation

**Purpose**: Provide reduced functionality when components fail.

```python
def supervisor_with_degradation(state: ResilientState) -> dict:
    """
    Supervisor that degrades gracefully.

    Degradation levels:
    1. Full: All agents available
    2. Partial: Use cached responses or simpler models
    3. Minimal: Return basic error message
    """
    failed_agents = state.get("failed_agents", [])

    # Level 1: Full functionality
    if not failed_agents:
        return {"next_agent": "advanced_agent"}

    # Level 2: Partial functionality (use simpler agent)
    if len(failed_agents) == 1:
        logger.warning("Degrading to basic agent due to failures")
        return {"next_agent": "basic_agent"}

    # Level 3: Minimal functionality (cached/static response)
    logger.error("Multiple failures, using fallback response")
    return {"next_agent": "cached_response"}

def cached_response_agent(state: ResilientState) -> dict:
    """Fallback agent that returns cached/static response."""
    response = AIMessage(
        content="Service temporarily unavailable. Please try again later.",
        name="system"
    )
    return {"messages": [response]}
```

**Key Points**:
- Always provide some response, even if degraded
- Inform users about degraded service
- Use cached data when fresh data unavailable
- Prioritize availability over functionality

---

## Error Propagation

### Pattern: Error Aggregation

**Purpose**: Collect and summarize errors from multiple agents.

```python
from typing import List, Dict

class ErrorSummary(TypedDict):
    error_count: int
    errors_by_agent: Dict[str, List[str]]
    severity: str  # "low", "medium", "high", "critical"

def aggregate_errors(state: ResilientState) -> ErrorSummary:
    """
    Aggregate errors from multi-agent execution.

    Returns summary for logging and user notification.
    """
    failed_agents = state.get("failed_agents", [])
    error = state.get("error", "")

    # Group errors by agent
    errors_by_agent: Dict[str, List[str]] = {}
    for agent in failed_agents:
        if agent not in errors_by_agent:
            errors_by_agent[agent] = []
        if error:
            errors_by_agent[agent].append(error)

    # Determine severity
    error_count = len(failed_agents)
    if error_count == 0:
        severity = "low"
    elif error_count == 1:
        severity = "medium"
    elif error_count <= 3:
        severity = "high"
    else:
        severity = "critical"

    return {
        "error_count": error_count,
        "errors_by_agent": errors_by_agent,
        "severity": severity
    }

def error_reporter_node(state: ResilientState) -> dict:
    """Final node that reports error summary."""
    summary = aggregate_errors(state)

    if summary["severity"] in ("high", "critical"):
        logger.error(f"Critical workflow failure: {summary}")
        # Could send alert, create ticket, etc.

    report = f"Workflow completed with {summary['error_count']} errors ({summary['severity']} severity)"
    return {"messages": [AIMessage(content=report, name="system")]}
```

**Key Points**:
- Centralize error tracking
- Provide error summaries for debugging
- Different severity levels for different responses
- Enable monitoring and alerting

---

## Best Practices Summary

1. **Never Crash**: Wrap all agent calls in try-except
2. **Log Everything**: Error context is critical for debugging
3. **Limit Retries**: Prevent infinite loops and cascading failures
4. **Provide Fallbacks**: Always have a plan B (and C)
5. **Monitor Health**: Track failure rates, response times
6. **Test Failures**: Intentionally inject errors to verify handling
7. **Degrade Gracefully**: Partial functionality > complete failure

---

## Testing Error Scenarios

```python
# Test agent failure handling
def test_agent_failure():
    """Verify supervisor handles agent failure correctly."""
    # Inject error into state
    state = {
        "messages": [],
        "error": "Simulated agent failure",
        "failed_agents": ["primary"]
    }

    result = supervisor_with_fallback(state)
    assert result["next_agent"] == "fallback", "Should route to fallback"

# Test circuit breaker
def test_circuit_breaker_opens():
    """Verify circuit breaker opens after threshold."""
    breaker = CircuitBreaker(failure_threshold=3)

    # Record failures
    for _ in range(3):
        breaker.record_failure("agent")

    # Circuit should be open
    assert not breaker.call_allowed("agent"), "Circuit should be open"
```

---

## References

- LangGraph Error Handling: https://docs.langchain.com/oss/python/langgraph/error-handling
- Tenacity Library: https://tenacity.readthedocs.io/
- Circuit Breaker Pattern: https://martinfowler.com/bliki/CircuitBreaker.html
- See `SKILL.md` for basic error handling examples
- See `examples/03_supervisor_with_limits.py` for working code
