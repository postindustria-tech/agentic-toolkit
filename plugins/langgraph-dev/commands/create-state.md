---
name: create-state
description: Generate a TypedDict state schema with Pydantic validation and Annotated fields
argument-hint: state_name [--fields=field1:type1,field2:type2]
allowed-tools:
  - Read
  - Write
  - AskUserQuestion
---

# Create LangGraph State Schema

Generate a TypedDict state schema with proper type hints, Annotated fields, and optional Pydantic validation.

## Instructions for Claude

### 1. Gather Information

Ask user for:
- State class name (if not provided)
- State fields (if `--fields` not provided):
  - Field name
  - Type (str, int, float, List[...], dict, etc.)
  - Whether append-only (use `Annotated[List, operator.add]`)
  - Whether custom reducer needed

### 2. Read Settings

Check `.claude/langgraph-dev.local.md` for:
- `code_style` (pydantic_v2 or pydantic_v1)
- `include_type_hints` (default: true)
- `include_docstrings` (default: true)

### 3. Generate State Schema

Create file `{state_name.lower()}_state.py` with:

```python
from typing import TypedDict, List, Annotated, Optional
from langchain.schema import BaseMessage
import operator

class {StateName}(TypedDict):
    \"\"\"State schema for {state_name} workflow.\"\"\"
    # Add fields based on user input
    messages: Annotated[List[BaseMessage], operator.add]  # If append-only
    current_step: str
    # ... other fields
```

### 4. Add Validators (if Pydantic requested)

If user wants validation:
```python
from pydantic import BaseModel, Field, field_validator

class {StateName}State(BaseModel):
    messages: List[BaseMessage] = Field(description="Conversation messages")
    confidence: float = Field(ge=0, le=1, description="Confidence score 0-1")

    @field_validator('confidence')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v
```

### 5. Add Helper Functions

Include:
```python
def create_initial_state(**kwargs) -> {StateName}:
    \"\"\"Factory for creating initial state with defaults.\"\"\"
    return {
        "messages": [],
        "current_step": "start",
        **kwargs
    }

def validate_state(state: {StateName}) -> bool:
    \"\"\"Validate state integrity.\"\"\"
    # Add validation logic
    return True
```

### 6. Output Summary

Show:
- File created
- Fields defined
- Annotated fields (if any)
- Custom reducers (if any)
- Example usage

## Example Invocation

```
/langgraph-dev:create-state AgentState --fields=messages:List[BaseMessage],intent:str,confidence:float
```

Refer to **state-management** skill for patterns.
