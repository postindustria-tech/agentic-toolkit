---
name: Memory Store and Knowledge Management
description: This skill should be used when the user asks to "add memory to my agent", "implement persistent knowledge", "store facts across conversations", "add semantic search to memory", "remember user preferences", "build a knowledge base", "implement episodic memory", "add semantic memory", or mentions "Store interface", "cross-thread persistence", "InMemoryStore", "PostgreSQL store", "PostgresSaver", or "long-term memory". Provides comprehensive guidance for building persistent, searchable memory systems in LangGraph.
version: 0.1.0
---

# Memory Store and Knowledge Management

Build persistent, searchable memory systems for LangGraph agents using the Store interface.

## Overview

LangGraph's **Store** interface enables agents to:
- **Remember across conversations** - Persist data beyond single threads
- **Search semantically** - Find relevant memories using natural language
- **Isolate user data** - Organize memories with namespaces
- **Build knowledge** - Accumulate facts and concepts over time

Unlike checkpointing (which saves workflow state within a thread), the Store provides **cross-thread persistence** for long-term knowledge retention.

---

## Core Concepts

### 1. Store Interface

The Store is LangGraph's abstraction for persistent memory:

```python
from langgraph.store.memory import InMemoryStore

# Basic store (key-value only)
store = InMemoryStore()

# Store with semantic search
from langchain.embeddings import init_embeddings

embeddings = init_embeddings("openai:text-embedding-3-small")
store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 1536,
    }
)
```

**When to use**:
- User profiles and preferences
- Facts and knowledge bases
- Historical context across sessions
- Shared data between threads

### 2. Namespace Organization

Namespaces provide hierarchical isolation using tuples:

```python
# Namespace structure: (category, user_id, [subcategory])
user_facts = ("memories", "user_123")
user_prefs = ("preferences", "user_123")
global_kb = ("knowledge_base",)

# Store data
store.put(user_facts, "fact_1", {"text": "User loves Python"})
store.put(user_prefs, "pref_1", {"theme": "dark"})
store.put(global_kb, "concept_1", {"topic": "LangGraph basics"})
```

**Namespace patterns**:
- `("memories", user_id)` - Per-user facts
- `("preferences", user_id)` - User settings
- `("knowledge_base",)` - Global shared knowledge
- `("conversations", user_id, thread_id)` - Thread-specific episodic memory

### 3. Storing Data

Use `store.put(namespace, key, value)`:

```python
# Store with auto-generated key
store.put(
    ("memories", "user_123"),
    "mem_001",
    {
        "text": "User mentioned they're learning DSPy",
        "timestamp": "2026-01-13T10:00:00Z",
        "context": "onboarding conversation"
    }
)

# Store with indexing control
store.put(
    ("memories", "user_123"),
    "mem_002",
    {"text": "User completed tutorial"},
    index=False  # Don't embed this item
)
```

**Key points**:
- **Namespace**: Tuple for organizational hierarchy
- **Key**: Unique string identifier (UUID recommended)
- **Value**: Dictionary with memory content
- **Index parameter**: Optional control over semantic indexing

### 4. Semantic Search

Retrieve memories using natural language queries:

```python
# Search for relevant memories
results = store.search(
    ("memories", "user_123"),
    query="What programming languages does the user know?",
    limit=5
)

# Results are ranked by semantic similarity
for item in results:
    print(f"Memory: {item.value['text']}")
    print(f"Similarity: {item.score}")
```

**Search parameters**:
- **namespace**: Where to search
- **query**: Natural language search term
- **limit**: Maximum results (default: 10)
- **filter**: Optional metadata filters (see references)

### 5. Memory Types

**Semantic Memory** (facts and concepts):
```python
# Store facts
store.put(
    ("facts", user_id),
    key,
    {"fact": "Paris is the capital of France", "domain": "geography"}
)
```

**Episodic Memory** (events and history):
```python
# Store events
store.put(
    ("events", user_id),
    key,
    {
        "event": "User asked about deployment",
        "timestamp": "2026-01-13T10:00:00Z",
        "outcome": "Provided Platform guide"
    }
)
```

---

## Integration with StateGraph

### Pattern 1: Store in Node Functions

```python
from typing import TypedDict
from langgraph.graph import StateGraph
from langgraph.store.base import BaseStore

class AgentState(TypedDict):
    messages: list
    user_id: str

def remember_facts(state: AgentState, *, store: BaseStore) -> dict:
    """Extract and store facts from conversation."""
    last_message = state["messages"][-1].content

    # Extract fact (simplified - use LLM in practice)
    if "my name is" in last_message.lower():
        name = last_message.split("my name is")[-1].strip()
        store.put(
            ("facts", state["user_id"]),
            "name",
            {"fact": f"User's name is {name}"}
        )

    return {}

def recall_context(state: AgentState, *, store: BaseStore) -> dict:
    """Retrieve relevant memories before responding."""
    last_message = state["messages"][-1].content

    # Search for relevant facts
    memories = store.search(
        ("facts", state["user_id"]),
        query=last_message,
        limit=3
    )

    context = "\n".join([m.value["fact"] for m in memories])
    return {"context": context}

# Build graph with store
workflow = StateGraph(AgentState)
workflow.add_node("recall", recall_context)
workflow.add_node("remember", remember_facts)
# ... add edges

# Compile with store
app = workflow.compile(store=store)
```

### Pattern 2: Store in Config

```python
# Pass user_id through config
config = {
    "configurable": {
        "thread_id": "conversation-123",
        "user_id": "user_456"  # Available in state
    }
}

result = app.invoke(initial_state, config)
```

---

## Quick Start Example

```python
from langgraph.store.memory import InMemoryStore
from langchain.embeddings import init_embeddings

# 1. Create store with semantic search
embeddings = init_embeddings("openai:text-embedding-3-small")
store = InMemoryStore(index={"embed": embeddings, "dims": 1536})

# 2. Store user facts
user_id = "user_123"
store.put(
    ("memories", user_id),
    "mem_1",
    {"text": "User is learning LangGraph"}
)
store.put(
    ("memories", user_id),
    "mem_2",
    {"text": "User prefers Python over JavaScript"}
)

# 3. Search memories
results = store.search(
    ("memories", user_id),
    query="What is the user learning?",
    limit=2
)

for memory in results:
    print(memory.value["text"])
# Output:
# User is learning LangGraph
# User prefers Python over JavaScript
```

---

## Examples

### Progressive Learning Path

The `examples/` directory contains runnable code demonstrating memory patterns:

1. **`01_basic_store.py`** - Store and retrieve data without embeddings
2. **`02_semantic_memory.py`** - Add semantic search with embeddings
3. **`03_vector_search_patterns.py`** - Advanced search with filters and multi-field indexing
4. **`04_persistent_knowledge_agent.py`** - Complete agent with episodic and semantic memory

**Run examples**:
```bash
cd examples/
uv run python 01_basic_store.py
```

---

## Reference Documentation

### Deep-Dive Guides

- **`references/vector-search-patterns.md`** - Embedding strategies, similarity search, hybrid search, multi-field indexing, search optimization
- **`references/production-memory-systems.md`** - Scaling, multi-user isolation, memory pruning, PostgreSQL backend, performance tuning

### Key Topics in References

**Vector Search Patterns**:
- Choosing embedding models
- Hybrid search (semantic + keyword)
- Multi-field indexing strategies
- Re-ranking results
- Search performance optimization

**Production Systems**:
- PostgreSQL-backed Store (persistent across restarts)
- Multi-tenant namespace design
- Memory pruning strategies
- Monitoring and analytics
- Security and data isolation

---

## Best Practices

### 1. Namespace Design

✅ **Good** - Clear hierarchy and isolation:
```python
("memories", user_id, "facts")
("memories", user_id, "preferences")
("knowledge_base", "domain_name")
```

❌ **Bad** - Flat structure mixes concerns:
```python
("all_data",)  # No isolation
("user_123_facts",)  # User ID in string, hard to query
```

### 2. Key Generation

✅ **Good** - UUIDs for uniqueness:
```python
import uuid
key = str(uuid.uuid4())
store.put(namespace, key, value)
```

❌ **Bad** - Sequential IDs risk conflicts:
```python
key = "mem_1"  # Collision risk
```

### 3. Embedding Efficiency

✅ **Good** - Index only searchable fields:
```python
store.put(
    namespace,
    key,
    {"memory": "...", "metadata": "...", "timestamp": "..."},
    index=["memory"]  # Only embed memory field
)
```

❌ **Bad** - Embed everything:
```python
# Embeds all fields including non-semantic data
store.put(namespace, key, data)  # Wastes tokens and storage
```

### 4. Search Specificity

✅ **Good** - Specific queries:
```python
store.search(
    ("memories", user_id),
    query="What programming languages does the user prefer?",
    limit=3
)
```

❌ **Bad** - Vague queries:
```python
store.search(
    ("memories", user_id),
    query="user info",  # Too broad
    limit=50  # Too many results
)
```

---

## Common Patterns

### User Profile Memory

```python
def save_user_preference(user_id: str, pref_type: str, value: any, store: BaseStore):
    """Save user preference."""
    store.put(
        ("preferences", user_id),
        pref_type,
        {"value": value, "updated_at": datetime.now().isoformat()}
    )

def get_user_preferences(user_id: str, store: BaseStore) -> dict:
    """Get all user preferences."""
    items = store.search(("preferences", user_id), limit=100)
    return {item.key: item.value["value"] for item in items}
```

### Knowledge Base

```python
def add_to_knowledge_base(topic: str, content: str, store: BaseStore):
    """Add concept to shared knowledge base."""
    store.put(
        ("knowledge_base", topic),
        str(uuid.uuid4()),
        {
            "content": content,
            "topic": topic,
            "created_at": datetime.now().isoformat()
        }
    )

def query_knowledge_base(query: str, store: BaseStore, limit: int = 5):
    """Search knowledge base."""
    return store.search(
        ("knowledge_base",),
        query=query,
        limit=limit
    )
```

### Conversation History

```python
def log_conversation_turn(user_id: str, thread_id: str, turn: dict, store: BaseStore):
    """Log conversation turn for episodic memory."""
    store.put(
        ("conversations", user_id, thread_id),
        str(uuid.uuid4()),
        {
            "user_message": turn["user"],
            "assistant_message": turn["assistant"],
            "timestamp": datetime.now().isoformat()
        },
        index=["user_message"]  # Only index user messages
    )
```

---

## Troubleshooting

### Store not persisting data

**Problem**: Data disappears after restart

**Solution**: InMemoryStore is ephemeral. Use PostgreSQL-backed store for production:
```python
# See references/production-memory-systems.md
from langgraph.store.postgres import PostgresStore
store = PostgresStore(connection_string="postgresql://...")
```

### Semantic search returns irrelevant results

**Problem**: Search returns unrelated memories

**Solutions**:
1. Check embedding model quality (use `text-embedding-3-small` or better)
2. Ensure indexed fields contain semantic content
3. Add metadata filters to narrow search space
4. Increase `limit` to see more candidates
5. Use multi-field indexing to target specific fields

### Namespace collision

**Problem**: Different users see each other's data

**Solution**: Always include `user_id` in namespace:
```python
# Correct
namespace = ("memories", user_id)

# Incorrect - global namespace
namespace = ("memories",)
```

---

## See Also

- **`graph-construction`** - Building graphs that use Store in nodes
- **`state-management`** - State vs Store (when to use each)
- **`subgraphs-and-composition`** - Passing Store to subgraphs

---

## Official Documentation

- [Cross-Thread Persistence (functional API)](https://langchain-ai.github.io/langgraph/how-tos/cross-thread-persistence-functional/)
- [Semantic Search in Memory](https://langchain-ai.github.io/langgraph/how-tos/memory/semantic-search/)
- [LangGraph Store API](https://langchain-ai.github.io/langgraph/reference/store/)

---

**Created**: 2026-01-13
**LangGraph Version**: 0.2.32+
**Status**: Active
