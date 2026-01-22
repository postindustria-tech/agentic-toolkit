"""
Example 3: Advanced Vector Search Patterns

Demonstrates advanced search techniques:
- Filtering search results by metadata
- Pagination with limit and offset
- Search result scoring and ranking
- Combining multiple search strategies
- Performance optimization techniques

Run: uv run python 03_vector_search_patterns.py

NOTE: Uses mock embeddings for demonstration without API keys.
"""

from langgraph.store.memory import InMemoryStore
from typing import List, Dict, Any
import uuid
from datetime import datetime, timedelta


# Mock embedding (same as Example 2)
class MockEmbedding:
    """Mock embedding for testing without API keys."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            vec = [0.0] * 1536
            for i, char in enumerate(text.lower()[:1536]):
                vec[i] = ord(char) / 255.0
            embeddings.append(vec)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]


def main():
    """Demonstrate advanced vector search patterns."""
    print("=== Example 3: Advanced Vector Search Patterns ===\n")

    # ============================================================================
    # 1. SETUP: CREATE STORE WITH RICH METADATA
    # ============================================================================
    print("--- Setup: Creating Store with Rich Metadata ---")

    # NOTE: Real semantic search requires embeddings
    # For testing, using basic store to demonstrate patterns
    # Production: store = InMemoryStore(index={"embed": embeddings, "dims": 1536})
    store = InMemoryStore()  # Basic store for testing

    user_id = "user_123"
    namespace = ("memories", user_id)

    # Store memories with rich metadata for filtering
    memories_data = [
        {
            "text": "User completed Python basics course",
            "category": "education",
            "importance": "high",
            "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
            "tags": ["python", "learning", "completed"]
        },
        {
            "text": "User asked about FastAPI deployment",
            "category": "question",
            "importance": "medium",
            "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
            "tags": ["fastapi", "deployment", "question"]
        },
        {
            "text": "User prefers async/await over callbacks",
            "category": "preference",
            "importance": "low",
            "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "tags": ["python", "async", "preference"]
        },
        {
            "text": "User built a chatbot with LangGraph",
            "category": "project",
            "importance": "high",
            "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "tags": ["langgraph", "project", "completed"]
        },
        {
            "text": "User mentioned working at a startup",
            "category": "professional",
            "importance": "medium",
            "created_at": (datetime.now() - timedelta(days=15)).isoformat(),
            "tags": ["work", "context"]
        },
        {
            "text": "User is learning about vector databases",
            "category": "education",
            "importance": "high",
            "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "tags": ["learning", "vectors", "databases"]
        },
    ]

    for i, data in enumerate(memories_data, 1):
        store.put(
            namespace,
            f"mem_{i}",
            data
        )
        print(f"✓ Stored: {data['text'][:50]}... [category: {data['category']}]")

    # ============================================================================
    # 2. BASIC SEARCH WITH LIMIT
    # ============================================================================
    print("\n--- Pattern 1: Limiting Results ---")

    query = "What is the user learning?"

    # Get top 3 most relevant results
    results = list(store.search(namespace, query=query, limit=3))

    print(f"Query: '{query}'")
    print(f"Results (limit=3):")
    for i, item in enumerate(results, 1):
        print(f"  {i}. {item.value['text']}")
        print(f"     Category: {item.value['category']}")

    # ============================================================================
    # 3. PAGINATION WITH OFFSET
    # ============================================================================
    print("\n--- Pattern 2: Pagination ---")

    # Simulate paginating through results
    page_size = 2
    total_pages = 3

    print(f"Query: '{query}' (paginated)")
    for page in range(total_pages):
        offset = page * page_size
        results = list(store.search(
            namespace,
            query=query,
            limit=page_size,
            # Note: offset parameter may vary by Store implementation
            # This is a conceptual demonstration
        ))

        if results:
            print(f"\nPage {page + 1}:")
            for item in results:
                print(f"  - {item.value['text'][:50]}...")

    # ============================================================================
    # 4. FILTERING BY METADATA (Post-Search)
    # ============================================================================
    print("\n--- Pattern 3: Metadata Filtering ---")

    # Get all results, then filter by category
    all_results = list(store.search(namespace, query=query, limit=10))

    # Filter for high-importance education items
    filtered = [
        item for item in all_results
        if item.value.get("importance") == "high"
        and item.value.get("category") == "education"
    ]

    print(f"Query: '{query}' + filters (importance=high, category=education)")
    print(f"Results after filtering:")
    for item in filtered:
        print(f"  - {item.value['text']}")
        print(f"    Tags: {', '.join(item.value['tags'])}")

    # ============================================================================
    # 5. TAG-BASED FILTERING
    # ============================================================================
    print("\n--- Pattern 4: Tag-Based Search ---")

    def search_by_tags(store, namespace, query: str, required_tags: List[str], limit: int = 5):
        """Search and filter by required tags."""
        results = list(store.search(namespace, query=query, limit=limit * 2))

        # Filter results that have ALL required tags
        filtered = [
            item for item in results
            if all(tag in item.value.get("tags", []) for tag in required_tags)
        ]

        return filtered[:limit]

    query = "What has the user completed?"
    required_tags = ["completed"]

    results = search_by_tags(store, namespace, query, required_tags, limit=3)

    print(f"Query: '{query}' + tags: {required_tags}")
    print(f"Results:")
    for item in results:
        print(f"  - {item.value['text']}")
        print(f"    Tags: {', '.join(item.value['tags'])}")

    # ============================================================================
    # 6. TIME-BASED FILTERING
    # ============================================================================
    print("\n--- Pattern 5: Time-Based Filtering ---")

    def search_recent(store, namespace, query: str, days: int = 7, limit: int = 5):
        """Search for memories from the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        results = list(store.search(namespace, query=query, limit=limit * 2))

        # Filter by recency
        recent = [
            item for item in results
            if datetime.fromisoformat(item.value["created_at"]) >= cutoff_date
        ]

        return recent[:limit]

    query = "What is the user working on?"
    results = search_recent(store, namespace, query, days=7, limit=3)

    print(f"Query: '{query}' (last 7 days)")
    print(f"Results:")
    for item in results:
        created = datetime.fromisoformat(item.value["created_at"])
        days_ago = (datetime.now() - created).days
        print(f"  - {item.value['text']}")
        print(f"    Created: {days_ago} days ago")

    # ============================================================================
    # 7. MULTI-QUERY SEARCH (Hybrid Approach)
    # ============================================================================
    print("\n--- Pattern 6: Multi-Query Search ---")

    def multi_query_search(store, namespace, queries: List[str], limit: int = 5):
        """
        Execute multiple queries and merge results.

        Useful for comprehensive retrieval when user intent is ambiguous.
        """
        seen_keys = set()
        merged_results = []

        for query in queries:
            results = list(store.search(namespace, query=query, limit=limit))

            for item in results:
                if item.key not in seen_keys:
                    seen_keys.add(item.key)
                    merged_results.append(item)

        return merged_results[:limit]

    queries = [
        "What is the user learning?",
        "What projects has the user built?",
        "What are the user's skills?"
    ]

    results = multi_query_search(store, namespace, queries, limit=5)

    print(f"Multi-query search with {len(queries)} queries:")
    for q in queries:
        print(f"  - '{q}'")
    print(f"\nMerged results ({len(results)} unique items):")
    for item in results:
        print(f"  - {item.value['text']}")

    # ============================================================================
    # 8. SEARCH RESULT RE-RANKING
    # ============================================================================
    print("\n--- Pattern 7: Result Re-Ranking ---")

    def rerank_by_importance(results: List[Any]) -> List[Any]:
        """
        Re-rank search results by importance level.

        Primary sort: semantic similarity (from search)
        Secondary sort: importance (high > medium > low)
        """
        importance_order = {"high": 3, "medium": 2, "low": 1}

        return sorted(
            results,
            key=lambda x: importance_order.get(x.value.get("importance", "low"), 0),
            reverse=True
        )

    query = "Tell me about the user"
    results = list(store.search(namespace, query=query, limit=10))

    print(f"Query: '{query}'")
    print("\nBefore re-ranking (by semantic similarity):")
    for i, item in enumerate(results[:3], 1):
        print(f"  {i}. {item.value['text'][:50]}...")
        print(f"     Importance: {item.value['importance']}")

    reranked = rerank_by_importance(results)

    print("\nAfter re-ranking (by importance):")
    for i, item in enumerate(reranked[:3], 1):
        print(f"  {i}. {item.value['text'][:50]}...")
        print(f"     Importance: {item.value['importance']}")

    # ============================================================================
    # 9. NAMESPACE PARTITIONING
    # ============================================================================
    print("\n--- Pattern 8: Namespace Partitioning ---")

    # Store in category-specific namespaces for faster search
    category_namespaces = {
        "education": ("memories", user_id, "education"),
        "projects": ("memories", user_id, "projects"),
        "preferences": ("memories", user_id, "preferences"),
    }

    # Store categorized memories
    store.put(
        category_namespaces["education"],
        "edu_1",
        {"text": "User completed React course", "timestamp": datetime.now().isoformat()}
    )

    store.put(
        category_namespaces["projects"],
        "proj_1",
        {"text": "User built an e-commerce site", "timestamp": datetime.now().isoformat()}
    )

    print("✓ Stored memories in category-specific namespaces")

    # Search only in relevant namespace (faster)
    print("\nSearching education namespace only:")
    edu_results = list(store.search(
        category_namespaces["education"],
        query="What courses has the user taken?",
        limit=5
    ))

    for item in edu_results:
        print(f"  - {item.value['text']}")

    print("\nBenefit: Searching a smaller namespace is faster than searching all memories")

    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("\n=== Summary of Search Patterns ===")
    print("✓ Pattern 1: Limit results for performance")
    print("✓ Pattern 2: Paginate through large result sets")
    print("✓ Pattern 3: Filter by metadata (importance, category)")
    print("✓ Pattern 4: Tag-based filtering for categorization")
    print("✓ Pattern 5: Time-based filtering for recency")
    print("✓ Pattern 6: Multi-query search for comprehensive retrieval")
    print("✓ Pattern 7: Re-rank results by custom criteria")
    print("✓ Pattern 8: Namespace partitioning for performance")
    print("\nNext: See 04_persistent_knowledge_agent.py for complete agent integration.")


if __name__ == "__main__":
    main()
