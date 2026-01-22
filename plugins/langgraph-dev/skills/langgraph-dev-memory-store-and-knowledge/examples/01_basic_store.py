"""
Example 1: Basic Store Usage

Demonstrates core Store operations without semantic search:
- Creating InMemoryStore
- Organizing data with namespaces
- Storing and retrieving items
- Basic search by metadata

Run: uv run python 01_basic_store.py
"""

from langgraph.store.memory import InMemoryStore
import uuid
from datetime import datetime


def main():
    """Demonstrate basic Store operations."""
    print("=== Example 1: Basic Store Usage ===\n")

    # ============================================================================
    # 1. CREATE STORE (no embeddings - key-value only)
    # ============================================================================
    store = InMemoryStore()
    print("✓ Created InMemoryStore (no semantic search)")

    # ============================================================================
    # 2. NAMESPACE ORGANIZATION
    # ============================================================================
    # Namespaces are tuples that provide hierarchical isolation
    user_id = "user_123"
    namespace_facts = ("memories", user_id, "facts")
    namespace_prefs = ("preferences", user_id)
    namespace_global = ("knowledge_base",)

    print(f"\nNamespaces created:")
    print(f"  - User facts: {namespace_facts}")
    print(f"  - User prefs: {namespace_prefs}")
    print(f"  - Global KB: {namespace_global}")

    # ============================================================================
    # 3. STORING DATA
    # ============================================================================
    print("\n--- Storing Data ---")

    # Store user facts
    store.put(
        namespace_facts,
        "fact_1",
        {
            "text": "User is learning LangGraph",
            "category": "education",
            "timestamp": datetime.now().isoformat()
        }
    )
    print("✓ Stored: User is learning LangGraph")

    store.put(
        namespace_facts,
        "fact_2",
        {
            "text": "User prefers Python over JavaScript",
            "category": "preferences",
            "timestamp": datetime.now().isoformat()
        }
    )
    print("✓ Stored: User prefers Python")

    store.put(
        namespace_facts,
        "fact_3",
        {
            "text": "User works as a software engineer",
            "category": "professional",
            "timestamp": datetime.now().isoformat()
        }
    )
    print("✓ Stored: User profession")

    # Store user preferences
    store.put(
        namespace_prefs,
        "theme",
        {"value": "dark", "updated_at": datetime.now().isoformat()}
    )
    print("✓ Stored: Theme preference")

    store.put(
        namespace_prefs,
        "language",
        {"value": "en", "updated_at": datetime.now().isoformat()}
    )
    print("✓ Stored: Language preference")

    # Store global knowledge
    store.put(
        namespace_global,
        str(uuid.uuid4()),
        {
            "topic": "LangGraph",
            "content": "LangGraph is a framework for building stateful workflows",
            "source": "official docs"
        }
    )
    print("✓ Stored: Global knowledge about LangGraph")

    # ============================================================================
    # 4. RETRIEVING DATA
    # ============================================================================
    print("\n--- Retrieving Data ---")

    # Get specific item by key
    item = store.get(namespace_facts, "fact_1")
    if item:
        print(f"Retrieved fact_1: {item.value['text']}")

    # Get all items in namespace (no query parameter = get all)
    print("\nAll user facts:")
    facts = store.search(namespace_facts, limit=10)
    for fact in facts:
        print(f"  - {fact.value['text']} (category: {fact.value['category']})")

    print("\nAll user preferences:")
    prefs = store.search(namespace_prefs, limit=10)
    for pref in prefs:
        print(f"  - {pref.key}: {pref.value['value']}")

    # ============================================================================
    # 5. NAMESPACE ISOLATION
    # ============================================================================
    print("\n--- Namespace Isolation ---")

    # Create data for a different user
    user_2_namespace = ("memories", "user_456", "facts")
    store.put(
        user_2_namespace,
        "fact_1",
        {"text": "User is learning React", "category": "education"}
    )

    # Search only returns items from the specified namespace
    user_1_facts = store.search(namespace_facts, limit=10)
    user_2_facts = store.search(user_2_namespace, limit=10)

    print(f"User 123 has {len(list(user_1_facts))} facts")
    print(f"User 456 has {len(list(user_2_facts))} facts")
    print("✓ Namespaces properly isolate user data")

    # ============================================================================
    # 6. UPDATING DATA
    # ============================================================================
    print("\n--- Updating Data ---")

    # Update by putting with same key
    store.put(
        namespace_prefs,
        "theme",
        {"value": "light", "updated_at": datetime.now().isoformat()}
    )
    print("✓ Updated theme preference to 'light'")

    # Verify update
    updated_theme = store.get(namespace_prefs, "theme")
    print(f"Current theme: {updated_theme.value['value']}")

    # ============================================================================
    # 7. DELETING DATA
    # ============================================================================
    print("\n--- Deleting Data ---")

    # Delete specific item
    store.delete(namespace_facts, "fact_3")
    print("✓ Deleted fact_3")

    # Verify deletion
    facts_after_delete = list(store.search(namespace_facts, limit=10))
    print(f"Facts remaining: {len(facts_after_delete)}")

    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("\n=== Summary ===")
    print("✓ Created InMemoryStore without embeddings")
    print("✓ Organized data with hierarchical namespaces")
    print("✓ Stored items with store.put(namespace, key, value)")
    print("✓ Retrieved items with store.get() and store.search()")
    print("✓ Demonstrated namespace isolation between users")
    print("✓ Updated and deleted items")
    print("\nNOTE: This store has no semantic search capability.")
    print("See 02_semantic_memory.py for embeddings-based search.")


if __name__ == "__main__":
    main()
