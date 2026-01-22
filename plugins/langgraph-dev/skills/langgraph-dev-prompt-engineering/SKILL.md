---
name: prompt-engineering-for-langgraph
description: This skill should be used when the user asks about "prompt template", "few-shot", "system prompt", "prompt engineering", "ChatPromptTemplate", "MessagesPlaceholder", "chat history", "format instructions", "LangGraph prompts", or needs guidance on crafting effective prompts for LangGraph workflows.
version: 0.3.2
---

## Requirements

- langchain-core >= 0.3.0
- langchain-anthropic >= 1.1.0 (for ChatAnthropic with native structured output via json_schema method)
- langgraph >= 1.0.0 (for StateGraph examples)

# Prompt Engineering for LangGraph

Effective prompts improve LLM behavior, accuracy, and reliability in LangGraph workflows.

## ChatPromptTemplate (Recommended)

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant specializing in {domain}."),
    ("human", "{user_input}")
])

# Initialize LLM
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# Use in chain
chain = prompt | llm
result = chain.invoke({"domain": "Python", "user_input": "Explain decorators"})
```

## MessagesPlaceholder for Conversation Memory

MessagesPlaceholder enables dynamic injection of conversation history into prompts - critical for LangGraph stateful workflows.

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Basic usage with chat history
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}")
])

# Invoke without history (optional=True allows this)
result = prompt.invoke({"input": "Hello!"})

# Invoke with history
result = prompt.invoke({
    "chat_history": [
        ("human", "What is 2+2?"),
        ("ai", "2+2 equals 4.")
    ],
    "input": "Now multiply that by 3"
})
```

### MessagesPlaceholder Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `variable_name` | str | required | Name of the variable for message list |
| `optional` | bool | False | If True, allows omitting the variable (returns empty list); if False, raises KeyError when variable missing |
| `n_messages` | int | None | Maximum number of messages to include |

### Shorthand Syntax

Use tuple syntax for implicit `optional=True`:

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),
    ("placeholder", "{chat_history}"),  # Equivalent to MessagesPlaceholder(variable_name="chat_history", optional=True)
    ("human", "{input}")
])
```

## LangGraph State Integration

Integrate prompts with LangGraph StateGraph nodes for stateful workflows.

```python
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_anthropic import ChatAnthropic

# Define state with message reducer
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: str

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an assistant. Context: {context}"),
    MessagesPlaceholder("messages"),
])

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# Node function using prompt with state
def assistant_node(state: AgentState) -> dict:
    formatted_prompt = prompt.invoke({
        "context": state["context"],
        "messages": state["messages"]
    })
    response = llm.invoke(formatted_prompt)
    return {"messages": [response]}

# Build graph
graph = StateGraph(AgentState)
graph.add_node("assistant", assistant_node)
graph.add_edge(START, "assistant")
graph.add_edge("assistant", END)

app = graph.compile()

# Run with initial state
result = app.invoke({
    "messages": [("human", "Hello!")],
    "context": "User is asking about Python"
})
```

## Few-Shot Learning

Provide 2-5 examples of desired input/output behavior to guide the LLM.

```python
from langchain_core.prompts import ChatPromptTemplate

few_shot_prompt = ChatPromptTemplate.from_messages([
    ("system", "Classify sentiment as positive, negative, or neutral."),
    ("human", "I love this product!"),
    ("ai", "Positive"),
    ("human", "This is the worst experience ever."),
    ("ai", "Negative"),
    ("human", "The weather is cloudy today."),
    ("ai", "Neutral"),
    ("human", "{text}")
])
```

## System Prompts

```python
from langchain_core.prompts import ChatPromptTemplate

system_prompt = """You are an expert code reviewer. Follow these guidelines:
1. Check for security vulnerabilities
2. Assess code readability
3. Suggest performance improvements
4. Be constructive and specific

Format your response as:
- Security: [analysis]
- Readability: [analysis]
- Performance: [analysis]
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "Review this code:\n{code}")
])
```

## Format Instructions

> **Note**: For modern LLMs with native function calling (Claude Sonnet 4.5, Claude Opus 4.5, Claude Haiku 4.5, GPT-4+), prefer `with_structured_output()` over text-based parsers. Output parsers remain useful for older models without native structured output support. See "Structured Output" section below.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import CommaSeparatedListOutputParser
from langchain_anthropic import ChatAnthropic

parser = CommaSeparatedListOutputParser()

prompt = ChatPromptTemplate.from_template(
    "List 5 {item}.\n\n{format_instructions}\n\nOutput:"
).partial(format_instructions=parser.get_format_instructions())

# Complete chain execution
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
chain = prompt | llm | parser

result = chain.invoke({"item": "programming languages"})
# result: ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust']
```

## Multi-Message Templates

Build complex conversation flows with multiple message types.

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a research assistant."),
    ("human", "Find information about {topic}"),
    ("ai", "I'll search for information on {topic}."),
    ("human", "Summarize the key findings")
])
```

## Dynamic Prompts

Generate task-specific prompts programmatically.

```python
from langchain_core.prompts import ChatPromptTemplate

def create_prompt(task_type: str) -> str:
    """Generate task-specific prompts."""
    if task_type == "classification":
        return "Classify the following text into categories..."
    elif task_type == "extraction":
        return "Extract key entities from the text..."
    else:
        return "Analyze the following text..."

# Define the task type before using it
task_type = "classification"
prompt = ChatPromptTemplate.from_template(create_prompt(task_type) + "\n\n{text}")
```

## Structured Output (Recommended for Modern LLMs)

Use `with_structured_output()` for reliable structured responses with LLMs that support native function calling.

```python
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic

class MovieReview(BaseModel):
    title: str = Field(description="The title of the movie being reviewed")
    rating: float = Field(description="Rating from 0.0 to 10.0")
    summary: str = Field(description="A brief summary of the review")

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# Pydantic model automatically guides LLM output format
llm_structured = llm.with_structured_output(MovieReview)

# Returns a MovieReview instance directly
result = llm_structured.invoke("Review the movie 'Inception'")
print(result.title, result.rating, result.summary)
```

### with_structured_output() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema` | Type | required | Pydantic model, TypedDict, or JSON schema defining output structure |
| `include_raw` | bool | False | If True, returns dict with `raw` (AIMessage), `parsed` (schema instance), and `parsing_error` (if any) |
| `method` | str | "function_calling" | Output method: "function_calling" or "json_schema" |

#### Using include_raw for Debugging

```python
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic

class Sentiment(BaseModel):
    label: str = Field(description="positive, negative, or neutral")
    confidence: float = Field(description="Confidence score 0.0-1.0")

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# include_raw=True returns both parsed output and raw response
llm_structured = llm.with_structured_output(Sentiment, include_raw=True)

result = llm_structured.invoke("I absolutely love this product!")
# result = {
#     "raw": AIMessage(content=..., tool_calls=...),
#     "parsed": Sentiment(label="positive", confidence=0.95),
#     "parsing_error": None
# }

# Access parsed result
sentiment = result["parsed"]
print(sentiment.label)  # "positive"

# Access raw response for debugging
raw_message = result["raw"]
print(raw_message.tool_calls)  # View tool call details
```

> **Tip**: Use specific model versions like `claude-sonnet-4-5-20250929` in production for consistent behavior. Model aliases like `claude-sonnet-4-5` automatically update to the latest snapshot.

## Best Practices

### 1. Be Specific

**Bad**: "Analyze this text"
**Good**: "Identify the main argument, supporting evidence, and conclusion in this text"

### 2. Provide Context

```python
prompt = """You are analyzing customer feedback for a SaaS product.
Your goal is to identify pain points and feature requests.

Customer feedback: {feedback}

Pain points:
Feature requests:"""
```

### 3. Use Examples (Few-Shot)

Include 2-5 examples of desired input→output behavior.

### 4. Step-by-Step Instructions

```python
prompt = """To classify this query, follow these steps:
1. Identify keywords related to known categories
2. Assess user intent (question, command, statement)
3. Select the most appropriate category
4. Assign confidence score

Query: {query}"""
```

### 5. Format Specifications

```python
prompt = """Respond in JSON format:
{
  "category": "string",
  "confidence": "float between 0 and 1",
  "reasoning": "brief explanation"
}

Input: {input}"""
```

## Task-Specific Prompts

### Classification

```python
"Classify the following text into one of these categories: {categories}\n\nText: {text}\nCategory:"
```

### Entity Extraction

```python
"Extract all person names, organizations, and locations from:\n{text}\n\nEntities:"
```

### Summarization

```python
"Summarize the following text in 2-3 sentences, focusing on key points:\n{text}\n\nSummary:"
```

## Official Documentation

- [LangChain Prompt Engineering Concepts](https://docs.langchain.com/langsmith/prompt-engineering-concepts)
- [LangChain Prompts API Reference](https://reference.langchain.com/python/langchain_core/prompts/)
- [LangChain Structured Output Documentation](https://docs.langchain.com/oss/python/langchain/structured-output)
- [LangGraph Prompt Generation Tutorial](https://langchain-ai.github.io/langgraph/tutorials/chatbots/information-gather-prompting/)
