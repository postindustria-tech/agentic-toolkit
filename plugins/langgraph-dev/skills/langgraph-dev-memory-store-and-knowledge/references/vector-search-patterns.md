# Vector Search Patterns for LangGraph Memory

Comprehensive guide to implementing effective semantic search in LangGraph Store.

## Contents

1. [Embedding Model Selection](#embedding-model-selection)
2. [Similarity Metrics](#similarity-metrics)
3. [Hybrid Search Strategies](#hybrid-search-strategies)
4. [Multi-Field Indexing](#multi-field-indexing)
5. [Search Optimization](#search-optimization)
6. [Re-Ranking Strategies](#re-ranking-strategies)

---

## Embedding Model Selection

### Popular Models (2026)

**OpenAI Models**:
- `text-embedding-3-small` (1536 dims) - Good balance of quality and cost
- `text-embedding-3-large` (3072 dims) - Higher quality, more expensive
- Best for: General-purpose semantic search

**Open Source Models**:
- `BAAI/bge-small-en-v1.5` (384 dims) - Efficient, good for local deployment
- `sentence-transformers/all-MiniLM-L6-v2` (384 dims) - Fast, lightweight
- Best for: Privacy-sensitive applications, local deployment

**Specialized Models**:
- `Cohere embed-english-v3.0` (1024 dims) - Optimized for retrieval
- `Voyage AI voyage-2` (1024 dims) - Strong performance on benchmarks
- Best for: Production RAG systems

### Selection Criteria

| Criterion | text-embedding-3-small | Open Source (BGE) | Cohere |
|-----------|----------------------|------------------|---------|
| **Cost** | Pay-per-token | Free (compute only) | Pay-per-token |
| **Quality** | High | Medium-High | Very High |
| **Privacy** | Cloud-based | On-premise | Cloud-based |
| **Speed** | Fast API | Very fast local | Fast API |
| **Dimensions** | 1536 | 384 | 1024 |

**Recommendation**: Start with `text-embedding-3-small` for prototyping, evaluate open-source models for production cost savings.

---

## LangGraph Store Configuration

### Basic Configuration

```python
from langchain.embeddings import init_embeddings
from langgraph.store.memory import InMemoryStore

# Initialize embedding model
embeddings = init_embeddings("openai:text-embedding-3-small")

# Create store with semantic search
store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 1536,  # Match embedding model dimensions
    }
)
```

### Multi-Model Configuration

```python
# Use different models for different namespaces
# (Store only supports one embedding model per instance)

# Option 1: Multiple Store instances
store_general = InMemoryStore(
    index={"embed": init_embeddings("openai:text-embedding-3-small"), "dims": 1536}
)

store_code = InMemoryStore(
    index={"embed": init_embeddings("voyage:voyage-code-2"), "dims": 1536}
)

# Option 2: Single store with namespace-based logic
# (Implement custom embedding selection in your application layer)
```

---

## Similarity Metrics

### Cosine Similarity (Default)

**How it works**: Measures angle between vectors, range [-1, 1]

**Formula**: `similarity = (A · B) / (||A|| ||B||)`

**Characteristics**:
- Ignores vector magnitude
- Best for normalized embeddings
- Standard for most embedding models

**When to use**:
- ✅ General semantic search
- ✅ OpenAI, Cohere, Voyage embeddings
- ✅ Text similarity tasks

### Dot Product

**How it works**: Direct multiplication of vectors

**Formula**: `similarity = A · B`

**Characteristics**:
- Considers vector magnitude
- Faster than cosine (no normalization)
- Used by some specialized models

**When to use**:
- ✅ Pre-normalized embeddings
- ✅ Performance-critical applications
- ✅ Some open-source models (check docs)

### Euclidean Distance

**How it works**: L2 distance in vector space

**Formula**: `distance = sqrt(Σ(Ai - Bi)²)`

**Characteristics**:
- Lower distance = more similar
- Sensitive to vector magnitude
- Less common for embeddings

**When to use**:
- ✅ Specific research applications
- ❌ Generally not recommended for semantic search

**Note**: LangGraph Store uses cosine similarity by default. Other metrics require custom implementation or different vector database.

---

## Hybrid Search Strategies

### Pattern 1: Semantic + Keyword (BM25)

**Purpose**: Combine semantic understanding with exact keyword matching

**Architecture**:
```
User Query
    ↓
[Keyword Search] ----→ [Results Set A]
    ↓                        ↓
[Semantic Search] --→ [Results Set B]
    ↓                        ↓
[Merge + Rerank] --------→ [Final Results]
```

**Implementation with LangGraph Store**:

```python
def hybrid_search(
    store: BaseStore,
    namespace: tuple,
    query: str,
    limit: int = 10
):
    """
    Hybrid search combining semantic and keyword matching.

    1. Semantic search with embeddings
    2. Post-filter for keyword matches
    3. Boost scores for exact matches
    """
    # Semantic search (broader recall)
    semantic_results = list(store.search(
        namespace,
        query=query,
        limit=limit * 2  # Get more for filtering
    ))

    # Extract query keywords (simple approach)
    keywords = query.lower().split()

    # Score and re-rank
    scored_results = []
    for item in semantic_results:
        text = item.value.get("text", "").lower()

        # Base score (from semantic similarity)
        score = 1.0  # In real implementation, use item.score if available

        # Boost for keyword matches (simplified BM25)
        keyword_boost = sum(1 for kw in keywords if kw in text) / len(keywords)
        score += keyword_boost * 0.3  # 30% boost for keyword matches

        scored_results.append((score, item))

    # Sort by combined score
    scored_results.sort(key=lambda x: -x[0])

    return [item for _, item in scored_results[:limit]]
```

**When to use**:
- Queries with specific technical terms
- Domain-specific jargon
- Proper names or acronyms

### Pattern 2: Multi-Query Expansion

**Purpose**: Improve recall by rephrasing query

```python
def multi_query_search(
    store: BaseStore,
    namespace: tuple,
    original_query: str,
    limit: int = 5
):
    """
    Generate query variations and merge results.

    In production, use LLM to generate query variations:
        variations = llm.invoke(f"Generate 3 variations of: {original_query}")
    """
    # Query variations (in production, use LLM)
    queries = [
        original_query,
        # Add variations that preserve meaning but use different words
    ]

    seen_keys = set()
    merged = []

    for query in queries:
        results = store.search(namespace, query=query, limit=limit)

        for item in results:
            if item.key not in seen_keys:
                seen_keys.add(item.key)
                merged.append(item)

    return merged[:limit]
```

---

## Multi-Field Indexing

### Pattern 1: Targeted Field Indexing

**Purpose**: Index only semantic-rich fields, skip metadata

```python
store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 1536,
        "fields": ["content", "summary"]  # Only index these fields
    }
)

# Store with multiple fields
store.put(
    namespace,
    key,
    {
        "content": "Long technical article about LangGraph...",
        "summary": "LangGraph tutorial for beginners",
        "author": "Jane Doe",  # Not indexed
        "created_at": "2026-01-13",  # Not indexed
        "tags": ["langgraph", "tutorial"]  # Not indexed
    }
)

# Search matches content and summary, not metadata
results = store.search(namespace, query="beginner tutorial")
```

**Benefits**:
- Faster indexing (fewer fields to embed)
- Lower costs (fewer tokens)
- More relevant results (focused on semantic content)

### Pattern 2: Per-Item Index Control

```python
# Index this item (default behavior)
store.put(
    namespace,
    "fact_1",
    {"text": "User prefers Python", "type": "preference"}
)

# Don't index this item (metadata only)
store.put(
    namespace,
    "meta_1",
    {"text": "User logged in at 10:00 AM", "type": "event"},
    index=False  # Skip embedding
)

# Index only specific field
store.put(
    namespace,
    "doc_1",
    {"title": "...", "content": "...", "metadata": "..."},
    index=["content"]  # Only embed content field
)
```

**Use cases**:
- Metadata records (timestamps, IDs) - `index=False`
- Mixed content types - selective field indexing
- Cost optimization - skip low-value content

---

## Search Optimization

### Pattern 1: Namespace Partitioning

**Purpose**: Reduce search space for faster queries

```python
# Bad: One namespace for everything
namespace = ("memories",)  # Searches all memories

# Good: Partition by category
namespaces = {
    "facts": ("memories", user_id, "facts"),
    "preferences": ("memories", user_id, "preferences"),
    "history": ("memories", user_id, "conversation_history")
}

# Search only relevant namespace
results = store.search(
    namespaces["facts"],  # Much smaller search space
    query="What does the user know about Python?"
)
```

**Performance Impact**:
- 10K total items, 1K in "facts" namespace → 10x faster search
- Lower memory usage during search
- Better result relevance (category-focused)

### Pattern 2: Search Result Caching

```python
from functools import lru_cache
import hashlib

def cache_key(namespace: tuple, query: str, limit: int) -> str:
    """Generate cache key for search."""
    key_str = f"{namespace}:{query}:{limit}"
    return hashlib.md5(key_str.encode()).hexdigest()

# Simple in-memory cache
@lru_cache(maxsize=100)
def cached_search(
    namespace: tuple,
    query: str,
    limit: int = 5
):
    """Cache search results for repeated queries."""
    # In production, implement cache invalidation on store.put()
    return list(store.search(namespace, query=query, limit=limit))
```

**When to use**:
- Repeated queries (e.g., "What is the user's name?")
- Chatbot applications with common questions
- Read-heavy workloads

**Cache Invalidation**:
```python
# Clear cache when data changes
cached_search.cache_clear()

# Or implement TTL-based caching with Redis
```

### Pattern 3: Limit Tuning

```python
# ❌ Bad: Retrieving too many results
results = store.search(namespace, query="...", limit=100)
# Slower, more irrelevant results, higher memory usage

# ✅ Good: Retrieve top-k most relevant
results = store.search(namespace, query="...", limit=5)
# Faster, more relevant, lower memory

# ✅ Better: Adaptive limit based on query type
def adaptive_limit(query: str) -> int:
    """Adjust limit based on query complexity."""
    if "list" in query.lower() or "all" in query.lower():
        return 20  # User wants comprehensive results
    return 5  # User wants specific answer
```

---

## Re-Ranking Strategies

### Pattern 1: Metadata Boosting

**Purpose**: Boost results based on metadata (recency, importance)

```python
from datetime import datetime, timedelta

def rerank_by_recency(results, boost_factor: float = 1.5):
    """Boost recent items in search results."""
    cutoff = datetime.now() - timedelta(days=7)

    reranked = []
    for item in results:
        score = 1.0  # Base score (would be item.score in production)

        # Boost recent items
        created_at = datetime.fromisoformat(item.value.get("created_at", "2020-01-01"))
        if created_at >= cutoff:
            score *= boost_factor

        reranked.append((score, item))

    # Sort by boosted score
    reranked.sort(key=lambda x: -x[0])
    return [item for _, item in reranked]
```

### Pattern 2: LLM Re-Ranking

**Purpose**: Use LLM to re-rank top results for higher precision

```python
def llm_rerank(query: str, results, top_k: int = 3):
    """
    Use LLM to re-rank top search results.

    1. Retrieve top 20 with semantic search (high recall)
    2. Re-rank with LLM for precision
    """
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

    # Get candidates (semantic search)
    candidates = results[:20]

    # Ask LLM to rank
    prompt = f"""
    Query: {query}

    Rank these results by relevance (most relevant first):
    {chr(10).join([f"{i+1}. {item.value['text']}" for i, item in enumerate(candidates)])}

    Return only the numbers in order (e.g., "3, 1, 5, 2, 4...")
    """

    ranking = llm.invoke(prompt).content
    ranked_indices = [int(x.strip()) - 1 for x in ranking.split(",")]

    return [candidates[i] for i in ranked_indices[:top_k]]
```

**Trade-off**: Higher precision, but adds latency and cost. Use for critical queries only.

---

## Best Practices Summary

### Embedding Selection

1. ✅ Start with `text-embedding-3-small` for prototyping
2. ✅ Evaluate open-source models for cost savings
3. ✅ Match embedding dimensions in Store config
4. ✅ Use specialized models for domain-specific content

### Indexing

1. ✅ Index only semantic-rich fields
2. ✅ Use `index=False` for metadata
3. ✅ Partition namespaces by category
4. ✅ Control indexing per-item for cost optimization

### Search

1. ✅ Keep `limit` low (5-10) for faster results
2. ✅ Use hybrid search for keyword-sensitive queries
3. ✅ Cache frequent queries
4. ✅ Re-rank for precision when needed

### Performance

1. ✅ Monitor search latency and optimize hot paths
2. ✅ Use namespace partitioning for large datasets
3. ✅ Profile embedding costs and optimize indexing
4. ✅ Implement TTL for cache invalidation

---

## Common Pitfalls

❌ **Over-indexing**: Embedding every field wastes tokens
✅ **Solution**: Use `fields` parameter or `index=False`

❌ **Too many results**: `limit=100` slows search and reduces relevance
✅ **Solution**: Keep `limit=5-10`, use pagination for more

❌ **No cache invalidation**: Stale results after updates
✅ **Solution**: Implement TTL or clear cache on `store.put()`

❌ **Ignoring recency**: Old results rank higher than recent
✅ **Solution**: Re-rank by timestamp or boost recent items

---

## Production Checklist

- [ ] Embedding model selected and tested
- [ ] Dimensions match in Store config
- [ ] Fields parameter configured (only index semantic content)
- [ ] Namespace design reviewed (partitioning by category)
- [ ] Search limits tuned (5-10 for most queries)
- [ ] Caching implemented for repeated queries
- [ ] Re-ranking strategy defined (metadata, LLM, or both)
- [ ] Performance monitoring in place
- [ ] Cost tracking for embeddings

---

## References

- [Top Embedding Models 2026 Guide](https://artsmart.ai/blog/top-embedding-models-in-2025/)
- [Embedding Models Comparison (OpenAI vs Gemini vs Cohere)](https://research.aimultiple.com/embedding-models/)
- [Hybrid Retrieval Research (2025)](https://arxiv.org/html/2506.00049v1)
- [LangGraph Semantic Search Guide](https://langchain-ai.github.io/langgraph/how-tos/memory/semantic-search/)
- See `SKILL.md` for basic semantic search setup
- See `examples/02_semantic_memory.py` for working code
- See `examples/03_vector_search_patterns.py` for advanced techniques
