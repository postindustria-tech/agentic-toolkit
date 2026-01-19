"""
Validation Loop Example

This example demonstrates using interrupts in a while loop to repeatedly
request and validate user input until it meets the requirements.

Run this example:
    python examples/validation-loop.py
"""

from typing import TypedDict, Optional
import uuid

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command


# Define the graph state
class State(TypedDict):
    """State schema for the validation workflow."""
    user_name: Optional[str]
    user_age: Optional[int]
    user_email: Optional[str]
    validation_attempts: int


def collect_name(state: State) -> State:
    """Collect and validate user name."""
    print("\n📝 Collecting user name...")
    prompt = "What is your name?"
    attempts = 0

    while True:
        name = interrupt({
            "field": "name",
            "prompt": prompt,
            "attempt": attempts + 1
        })

        # Validation: non-empty string, at least 2 characters
        if isinstance(name, str) and len(name.strip()) >= 2:
            print(f"✅ Valid name: {name}")
            break
        else:
            attempts += 1
            prompt = f"❌ Invalid: '{name}'. Name must be at least 2 characters. Try again:"
            print(prompt)

    return {"user_name": name.strip(), "validation_attempts": attempts}


def collect_age(state: State) -> State:
    """Collect and validate user age."""
    print("\n📝 Collecting user age...")
    prompt = "What is your age?"
    attempts = 0

    while True:
        age = interrupt({
            "field": "age",
            "prompt": prompt,
            "attempt": attempts + 1,
            "hint": "Enter a number between 1 and 120"
        })

        # Validation: integer between 1 and 120
        if isinstance(age, int) and 1 <= age <= 120:
            print(f"✅ Valid age: {age}")
            break
        else:
            attempts += 1
            prompt = {
                "error": f"Invalid input: '{age}'",
                "message": "Age must be a number between 1 and 120. Try again:"
            }
            print(f"❌ {prompt['error']}")

    return {"user_age": age}


def collect_email(state: State) -> State:
    """Collect and validate user email."""
    print("\n📝 Collecting user email...")
    prompt = "What is your email address?"
    attempts = 0

    while True:
        email = interrupt({
            "field": "email",
            "prompt": prompt,
            "attempt": attempts + 1,
            "example": "user@example.com"
        })

        # Validation: contains @ and .
        if isinstance(email, str) and "@" in email and "." in email:
            print(f"✅ Valid email: {email}")
            break
        else:
            attempts += 1
            prompt = f"❌ Invalid email: '{email}'. Must contain @ and a domain. Try again:"
            print(prompt)

    return {"user_email": email}


def confirm_details(state: State) -> State:
    """Display collected information."""
    print("\n" + "=" * 60)
    print("📋 USER DETAILS COLLECTED")
    print("=" * 60)
    print(f"Name: {state['user_name']}")
    print(f"Age: {state['user_age']}")
    print(f"Email: {state['user_email']}")
    print(f"Total validation attempts: {state['validation_attempts']}")
    print("=" * 60)
    return state


# Build the graph
def build_validation_workflow():
    """Build the validation workflow graph."""
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("collect_name", collect_name)
    builder.add_node("collect_age", collect_age)
    builder.add_node("collect_email", collect_email)
    builder.add_node("confirm", confirm_details)

    # Define edges
    builder.add_edge(START, "collect_name")
    builder.add_edge("collect_name", "collect_age")
    builder.add_edge("collect_age", "collect_email")
    builder.add_edge("collect_email", "confirm")
    builder.add_edge("confirm", END)

    # Compile with checkpointer (required for interrupts)
    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


def main():
    """Run the validation loop example."""
    graph = build_validation_workflow()

    # Create a unique thread ID for this execution
    thread_id = f"validation-{uuid.uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}

    print("=" * 60)
    print("VALIDATION LOOP EXAMPLE")
    print("=" * 60)
    print("\nThis example demonstrates multi-turn validation with retries.")

    # Simulated user inputs (some invalid to demonstrate validation)
    user_inputs = [
        # Name attempts
        "",           # Invalid: too short
        "A",          # Invalid: too short
        "Alice",      # Valid!

        # Age attempts
        "not a number",  # Invalid: not an integer
        -5,              # Invalid: negative
        150,             # Invalid: too high
        25,              # Valid!

        # Email attempts
        "invalid",               # Invalid: no @
        "invalid@",              # Invalid: no domain
        "alice@example.com",     # Valid!
    ]

    input_index = 0

    # Run the workflow with simulated inputs
    result = graph.invoke({
        "user_name": None,
        "user_age": None,
        "user_email": None,
        "validation_attempts": 0
    }, config=config)

    # Process each interrupt
    while "__interrupt__" in result and input_index < len(user_inputs):
        interrupt_info = result["__interrupt__"][0]
        simulated_input = user_inputs[input_index]

        print(f"\n[Step {input_index + 1}] Field: {interrupt_info.value['field']}")
        print(f"   Simulated input: {repr(simulated_input)}")

        # Resume with simulated input
        result = graph.invoke(
            Command(resume=simulated_input),
            config=config
        )

        input_index += 1

    if "__interrupt__" not in result:
        print("\n✅ Workflow completed successfully!")
    else:
        print(f"\n⚠️ Workflow incomplete - ran out of simulated inputs")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
