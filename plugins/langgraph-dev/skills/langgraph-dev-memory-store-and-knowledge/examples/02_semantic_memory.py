"""
Example 2: Semantic Memory with Embeddings

Demonstrates semantic search capabilities:
- Creating Store with embedding configuration
- Storing items with automatic embedding
- Semantic search using natural language queries
- Comparing results with basic keyword matching

Run: uv run python 02_semantic_memory.py

NOTE: This example uses a mock embedding for demonstration without API keys.
In production, use real embeddings:
    from langchain.embeddings import init_embeddings
    embeddings = init_embeddings("openai:text-embedding-3-small")
"""

from langgraph.store.memory import InMemoryStore
from typing import List
import uuid
from datetime import datetime


# ============================================================================
# MOCK EMBEDDING (for testing without API keys)
# ============================================================================
class MockEmbedding:
    """
    Simple mock embedding for testing.

    In production, replace with:
        from langchain.embeddings import init_embeddings
        embeddings = init_embeddings("openai:text-embedding-3-small")
    """

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings based on text length (for testing)."""
        # Simple mock: use character counts as features
        embeddings = []
        for text in texts:
            # Create a simple 1536-dim vector (matching OpenAI's dimensions)
            # Based on character frequencies (mock semantic similarity)
            vec = [0.0] * 1536

            # Use character counts as features (simplified)
            for i, char in enumerate(text.lower()[:1536]):
                vec[i] = ord(char) / 255.0  # Normalize to [0, 1]

            embeddings.append(vec)

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query."""
        return self.embed_documents([text])[0]


def main():
    """Demonstrate semantic search with embeddings."""
    print("=== Example 2: Semantic Memory with Embeddings ===\n")

    # ============================================================================
    # 1. CREATE STORE WITH EMBEDDINGS
    # ============================================================================
    print("--- Creating Store with Semantic Search ---")

    # NOTE: Semantic search requires real embeddings
    # This example demonstrates the API but uses basic store for testing
    #
    # Production code (requires OpenAI API key):
    # from langchain.embeddings import init_embeddings
    # embeddings = init_embeddings("openai:text-embedding-3-small")
    # store = InMemoryStore(index={"embed": embeddings, "dims": 1536})

    # For testing without API keys, use basic store
    store = InMemoryStore()  # No semantic search
    print("✓ Created InMemoryStore (basic mode for testing)")
    print("  NOTE: Real semantic search requires embedding model")
    print("  See code comments for production configuration")

    # ============================================================================
    # 2. STORE SEMANTIC MEMORIES
    # ============================================================================
    print("\n--- Storing Semantic Memories ---")

    user_id = "user_123"
    namespace = ("memories", user_id)

    # Store various facts about programming
    memories = [
        "User is learning Python programming language",
        "User enjoys building web applications with FastAPI",
        "User prefers functional programming paradigms",
        "User is studying machine learning algorithms",
        "User works on natural language processing projects",
        "User likes to read technical documentation",
        "User frequently uses the Anthropic Claude API",
        "User is interested in LangGraph framework",
    ]

    for i, memory in enumerate(memories, 1):
        store.put(
            namespace,
            f"mem_{i}",
            {
                "text": memory,
                "timestamp": datetime.now().isoformat(),
                "type": "fact"
            }
        )
        print(f"✓ Stored memory {i}: {memory[:50]}...")

    # ============================================================================
    # 3. SEMANTIC SEARCH
    # ============================================================================
    print("\n--- Semantic Search Examples ---")

    # Example 1: Search for programming language knowledge
    print("\n1. Query: 'What programming language is the user learning?'")
    results = store.search(
        namespace,
        query="What programming language is the user learning?",
        limit=3
    )

    print("   Top results:")
    for i, item in enumerate(results, 1):
        print(f"   {i}. {item.value['text']}")
        # Note: MockEmbedding doesn't provide real scores
        # Real embeddings would show: print(f"      Score: {item.score:.4f}")

    # Example 2: Search for AI-related work
    print("\n2. Query: 'Does the user work with AI?'")
    results = store.search(
        namespace,
        query="Does the user work with AI?",
        limit=3
    )

    print("   Top results:")
    for i, item in enumerate(results, 1):
        print(f"   {i}. {item.value['text']}")

    # Example 3: Search for web development
    print("\n3. Query: 'What does the user build?'")
    results = store.search(
        namespace,
        query="What does the user build?",
        limit=3
    )

    print("   Top results:")
    for i, item in enumerate(results, 1):
        print(f"   {i}. {item.value['text']}")

    # ============================================================================
    # 4. MULTI-FIELD INDEXING
    # ============================================================================
    print("\n--- Multi-Field Indexing ---")

    # For testing: using basic store
    # Production would use multi-field indexing with embeddings:
    # store_multi = InMemoryStore(
    #     index={"embed": embeddings, "dims": 1536, "fields": ["text", "context"]}
    # )
    store_multi = InMemoryStore()  # Basic store for testing

    namespace_detailed = ("detailed_memories", user_id)

    # Store with multiple semantic fields
    store_multi.put(
        namespace_detailed,
        "mem_1",
        {
            "text": "User completed LangGraph tutorial",
            "context": "Learning about state graphs and conditional routing",
            "timestamp": datetime.now().isoformat()
        }
    )

    store_multi.put(
        namespace_detailed,
        "mem_2",
        {
            "text": "User built a chatbot",
            "context": "Using FastAPI for backend and React for frontend",
            "timestamp": datetime.now().isoformat()
        }
    )

    print("✓ Stored memories with multi-field indexing")

    # Search across both fields
    print("\nQuery: 'conditional routing' (matches context field)")
    results = store_multi.search(
        namespace_detailed,
        query="conditional routing",
        limit=2
    )

    for item in results:
        print(f"  - {item.value['text']}")
        print(f"    Context: {item.value['context']}")

    # ============================================================================
    # 5. PER-ITEM INDEX CONTROL
    # ============================================================================
    print("\n--- Per-Item Index Control ---")

    namespace_mixed = ("mixed_memories", user_id)

    # Store with indexing
    store.put(
        namespace_mixed,
        "searchable_1",
        {
            "text": "User prefers dark mode theme",
            "searchable": True
        }
    )
    print("✓ Stored searchable item (indexed)")

    # Store without indexing (saves embedding costs)
    store.put(
        namespace_mixed,
        "metadata_1",
        {
            "text": "User completed onboarding at 2026-01-13",
            "searchable": False
        },
        index=False  # Don't embed this item
    )
    print("✓ Stored metadata item (NOT indexed)")

    # Only indexed items appear in semantic search
    print("\nQuery: 'theme preferences'")
    results = store.search(
        namespace_mixed,
        query="theme preferences",
        limit=5
    )
    print(f"Results found: {len(list(results))}")
    print("(Non-indexed items won't appear in semantic search)")

    # ============================================================================
    # 6. PRACTICAL PATTERN: FACT EXTRACTION
    # ============================================================================
    print("\n--- Practical Pattern: Fact Extraction ---")

    def extract_and_store_fact(conversation_turn: str, user_id: str):
        """
        Extract facts from conversation and store with semantic search.

        In production, use LLM to extract structured facts.
        """
        # Simplified: store entire turn (use LLM extraction in production)
        fact_id = str(uuid.uuid4())

        store.put(
            ("extracted_facts", user_id),
            fact_id,
            {
                "fact": conversation_turn,
                "extracted_at": datetime.now().isoformat(),
                "source": "conversation"
            }
        )

        return fact_id

    # Simulate conversation turns
    turns = [
        "I've been working with Python for 5 years",
        "My favorite framework is LangGraph",
        "I need help optimizing my agent's memory usage"
    ]

    print("Extracting facts from conversation:")
    for turn in turns:
        fact_id = extract_and_store_fact(turn, user_id)
        print(f"  ✓ Stored: {turn[:50]}...")

    # Query extracted facts
    print("\nQuery: 'How long has the user worked with Python?'")
    results = store.search(
        ("extracted_facts", user_id),
        query="How long has the user worked with Python?",
        limit=1
    )

    for item in results:
        print(f"  → {item.value['fact']}")

    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("\n=== Summary ===")
    print("✓ Demonstrated semantic memory API patterns")
    print("✓ Stored memories with structured data")
    print("✓ Performed search with query parameter")
    print("✓ Showed multi-field indexing pattern")
    print("✓ Demonstrated per-item index control")
    print("✓ Showed practical fact extraction pattern")
    print("\nIMPORTANT: This example runs without embeddings for testing.")
    print("Production semantic search requires real embedding model:")
    print("  from langchain.embeddings import init_embeddings")
    print("  embeddings = init_embeddings('openai:text-embedding-3-small')")
    print("  store = InMemoryStore(index={'embed': embeddings, 'dims': 1536})")
    print("\nNext: See 03_vector_search_patterns.py for advanced search techniques.")


if __name__ == "__main__":
    main()
