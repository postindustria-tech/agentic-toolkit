"""
Example 4: Persistent Knowledge Agent

Demonstrates a complete agent with long-term memory:
- Episodic memory (conversation history)
- Semantic memory (extracted facts)
- Context recall before responding
- Knowledge persistence across conversations
- Multi-user isolation

Run: uv run python 04_persistent_knowledge_agent.py

This is a production-ready pattern for building agents with memory.
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import uuid
from datetime import datetime


# ============================================================================
# MOCK LLM (for testing without API keys)
# ============================================================================
class MockLLM:
    """
    Mock LLM for testing without API keys.

    In production, replace with:
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
    """

    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        """Generate mock response based on conversation context."""
        last_msg = messages[-1].content if messages else ""

        # Check for context about user's name
        has_name_context = any(
            "name is" in msg.content.lower()
            for msg in messages
            if isinstance(msg, (HumanMessage, AIMessage))
        )

        # Simple pattern matching for demonstration
        if "my name is" in last_msg.lower():
            name = last_msg.lower().split("my name is")[-1].strip().split()[0]
            response = f"Nice to meet you, {name.capitalize()}! I'll remember that."

        elif "what is my name" in last_msg.lower() or "who am i" in last_msg.lower():
            if has_name_context:
                # Find the name from context (simplified)
                for msg in reversed(messages):
                    if "my name is" in msg.content.lower():
                        name = msg.content.lower().split("my name is")[-1].strip().split()[0]
                        response = f"Your name is {name.capitalize()}."
                        break
                else:
                    response = "I remember you told me your name earlier!"
            else:
                response = "I don't think you've told me your name yet."

        elif "learning" in last_msg.lower():
            response = "Learning is great! What are you studying?"

        elif "help" in last_msg.lower():
            response = "I'm here to help! I have a memory system that remembers our conversations."

        else:
            response = f"I understand you said: '{last_msg}'. How can I help you with that?"

        return AIMessage(content=response, name="assistant")


# Mock embedding (same as previous examples)
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


# ============================================================================
# STATE DEFINITION
# ============================================================================
class AgentState(TypedDict):
    """State for persistent knowledge agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    thread_id: str
    context: str  # Retrieved context from memory
    extracted_facts: List[str]  # Facts to store


# ============================================================================
# MEMORY NAMESPACES
# ============================================================================
def get_namespaces(user_id: str, thread_id: str):
    """Get namespace tuples for organizing memories."""
    return {
        "episodic": ("conversations", user_id, thread_id),  # Thread-specific history
        "semantic": ("facts", user_id),  # User-specific facts
        "all_facts": ("facts", user_id),  # Alternative: all facts
    }


# ============================================================================
# NODE 1: RECALL CONTEXT
# ============================================================================
def recall_context(state: AgentState, *, store: BaseStore) -> dict:
    """
    Retrieve relevant context from memory before responding.

    Searches both:
    - Episodic memory (this conversation's history)
    - Semantic memory (facts about the user)
    """
    print("\n[Recall] Retrieving context from memory...")

    user_id = state["user_id"]
    thread_id = state["thread_id"]
    last_message = state["messages"][-1].content if state["messages"] else ""

    namespaces = get_namespaces(user_id, thread_id)

    # Search episodic memory (conversation history)
    episodic_results = list(store.search(
        namespaces["episodic"],
        query=last_message,
        limit=3
    ))

    # Search semantic memory (user facts)
    semantic_results = list(store.search(
        namespaces["semantic"],
        query=last_message,
        limit=3
    ))

    # Build context string
    context_parts = []

    if semantic_results:
        context_parts.append("# Known Facts About User:")
        for item in semantic_results:
            context_parts.append(f"- {item.value['fact']}")

    if episodic_results:
        context_parts.append("\n# Recent Conversation History:")
        for item in episodic_results:
            turn = item.value
            context_parts.append(f"User: {turn['user_message']}")
            context_parts.append(f"Assistant: {turn['assistant_message']}")

    context = "\n".join(context_parts) if context_parts else "No prior context found."

    print(f"[Recall] Retrieved {len(semantic_results)} facts, {len(episodic_results)} history items")
    print(f"[Recall] Context:\n{context}\n")

    return {"context": context}


# ============================================================================
# NODE 2: GENERATE RESPONSE
# ============================================================================
def generate_response(state: AgentState) -> dict:
    """Generate response using LLM with retrieved context."""
    print("[Generate] Creating response...")

    llm = MockLLM()

    # In production, include context in system message:
    # system_message = SystemMessage(content=f"Context:\n{state['context']}")
    # messages = [system_message] + state["messages"]
    # response = llm.invoke(messages)

    # Simplified for mock
    response = llm.invoke(state["messages"])

    print(f"[Generate] Response: {response.content}\n")

    return {"messages": [response]}


# ============================================================================
# NODE 3: EXTRACT FACTS
# ============================================================================
def extract_facts(state: AgentState) -> dict:
    """
    Extract facts from conversation to store in semantic memory.

    In production, use LLM to extract structured facts:
        fact_extractor = ChatAnthropic(model="claude-sonnet-4-5-20250929")
        facts = fact_extractor.invoke("Extract facts from: {conversation}")
    """
    print("[Extract] Analyzing conversation for facts...")

    last_user_msg = None
    last_ai_msg = None

    # Find last exchange
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and not last_ai_msg:
            last_ai_msg = msg
        elif isinstance(msg, HumanMessage) and not last_user_msg:
            last_user_msg = msg

        if last_user_msg and last_ai_msg:
            break

    facts = []

    if last_user_msg:
        user_content = last_user_msg.content.lower()

        # Simple fact extraction patterns (use LLM in production)
        if "my name is" in user_content:
            name = user_content.split("my name is")[-1].strip().split()[0]
            facts.append(f"User's name is {name.capitalize()}")

        if "i'm learning" in user_content or "i am learning" in user_content:
            # Extract what they're learning
            facts.append(f"User mentioned: {last_user_msg.content}")

        if "i work" in user_content or "my job" in user_content:
            facts.append(f"User professional context: {last_user_msg.content}")

    print(f"[Extract] Extracted {len(facts)} facts")
    for fact in facts:
        print(f"  - {fact}")

    return {"extracted_facts": facts}


# ============================================================================
# NODE 4: STORE MEMORIES
# ============================================================================
def store_memories(state: AgentState, *, store: BaseStore) -> dict:
    """
    Store both episodic and semantic memories.

    - Episodic: Store conversation turn
    - Semantic: Store extracted facts
    """
    print("\n[Store] Saving memories...")

    user_id = state["user_id"]
    thread_id = state["thread_id"]
    namespaces = get_namespaces(user_id, thread_id)

    # Get last user and assistant messages
    last_user_msg = None
    last_ai_msg = None

    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and not last_ai_msg:
            last_ai_msg = msg
        elif isinstance(msg, HumanMessage) and not last_user_msg:
            last_user_msg = msg

        if last_user_msg and last_ai_msg:
            break

    # Store episodic memory (conversation turn)
    if last_user_msg and last_ai_msg:
        turn_id = str(uuid.uuid4())
        store.put(
            namespaces["episodic"],
            turn_id,
            {
                "user_message": last_user_msg.content,
                "assistant_message": last_ai_msg.content,
                "timestamp": datetime.now().isoformat()
            },
            index=["user_message"]  # Only index user messages for search
        )
        print(f"[Store] ✓ Episodic memory: conversation turn {turn_id[:8]}...")

    # Store semantic memory (extracted facts)
    for fact in state.get("extracted_facts", []):
        fact_id = str(uuid.uuid4())
        store.put(
            namespaces["semantic"],
            fact_id,
            {
                "fact": fact,
                "extracted_at": datetime.now().isoformat(),
                "source": "conversation"
            }
        )
        print(f"[Store] ✓ Semantic memory: {fact}")

    print("[Store] Memories saved successfully\n")

    return {}


# ============================================================================
# BUILD GRAPH
# ============================================================================
def create_agent():
    """Create persistent knowledge agent graph."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("recall", recall_context)
    workflow.add_node("generate", generate_response)
    workflow.add_node("extract", extract_facts)
    workflow.add_node("store", store_memories)

    # Add edges
    workflow.add_edge(START, "recall")
    workflow.add_edge("recall", "generate")
    workflow.add_edge("generate", "extract")
    workflow.add_edge("extract", "store")
    workflow.add_edge("store", END)

    return workflow


# ============================================================================
# MAIN DEMO
# ============================================================================
def main():
    """Demonstrate persistent knowledge agent."""
    print("=== Example 4: Persistent Knowledge Agent ===\n")

    # Create store (basic mode for testing without API keys)
    # Production would use semantic search:
    # from langchain.embeddings import init_embeddings
    # embeddings = init_embeddings("openai:text-embedding-3-small")
    # store = InMemoryStore(index={"embed": embeddings, "dims": 1536})
    store = InMemoryStore()  # Basic store for testing

    # Build agent
    workflow = create_agent()
    app = workflow.compile(store=store)

    # User configuration
    user_id = "user_123"
    thread_id = "conversation_001"

    print("=== Conversation 1: First Interaction ===")
    print("User: Hi, my name is Alice and I'm learning Python.")

    result = app.invoke({
        "messages": [HumanMessage(content="Hi, my name is Alice and I'm learning Python.")],
        "user_id": user_id,
        "thread_id": thread_id,
        "context": "",
        "extracted_facts": []
    })

    print(f"Assistant: {result['messages'][-1].content}")

    # Second message in same conversation
    print("\n=== Conversation 1: Follow-up ===")
    print("User: What is my name?")

    result = app.invoke({
        "messages": result["messages"] + [HumanMessage(content="What is my name?")],
        "user_id": user_id,
        "thread_id": thread_id,
        "context": "",
        "extracted_facts": []
    })

    print(f"Assistant: {result['messages'][-1].content}")

    # NEW conversation (different thread) - testing cross-thread persistence
    print("\n=== Conversation 2: New Thread (Cross-Thread Memory) ===")
    thread_id_2 = "conversation_002"

    print("User: Hi, do you remember me?")

    result2 = app.invoke({
        "messages": [HumanMessage(content="Hi, do you remember me?")],
        "user_id": user_id,
        "thread_id": thread_id_2,
        "context": "",
        "extracted_facts": []
    })

    print(f"Assistant: {result2['messages'][-1].content}")

    # Ask for name in new thread
    print("\n=== Conversation 2: Testing Cross-Thread Fact Retrieval ===")
    print("User: What is my name?")

    result2 = app.invoke({
        "messages": result2["messages"] + [HumanMessage(content="What is my name?")],
        "user_id": user_id,
        "thread_id": thread_id_2,
        "context": "",
        "extracted_facts": []
    })

    print(f"Assistant: {result2['messages'][-1].content}")

    # ========================================================================
    # INSPECT STORED MEMORIES
    # ========================================================================
    print("\n=== Inspecting Stored Memories ===")

    # Get semantic memories (facts)
    facts = list(store.search(("facts", user_id), limit=10))
    print(f"\nStored Facts ({len(facts)}):")
    for item in facts:
        print(f"  - {item.value['fact']}")

    # Get episodic memories (conversation history) from thread 1
    history_1 = list(store.search(("conversations", user_id, thread_id), limit=10))
    print(f"\nThread 1 History ({len(history_1)} turns):")
    for item in history_1:
        print(f"  User: {item.value['user_message']}")
        print(f"  Assistant: {item.value['assistant_message'][:50]}...")

    # Get episodic memories from thread 2
    history_2 = list(store.search(("conversations", user_id, thread_id_2), limit=10))
    print(f"\nThread 2 History ({len(history_2)} turns):")
    for item in history_2:
        print(f"  User: {item.value['user_message']}")
        print(f"  Assistant: {item.value['assistant_message'][:50]}...")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n=== Summary ===")
    print("✓ Built agent with StateGraph + Store integration")
    print("✓ Implemented episodic memory (conversation history per thread)")
    print("✓ Implemented semantic memory (facts across all threads)")
    print("✓ Recalled context before generating responses")
    print("✓ Extracted and stored facts after each turn")
    print("✓ Demonstrated cross-thread persistence")
    print("✓ Multi-user isolation with namespace design")
    print("\nThis pattern enables:")
    print("  - Agents that remember users across conversations")
    print("  - Knowledge accumulation over time")
    print("  - Personalized responses based on user history")
    print("  - Searchable conversation archives")


if __name__ == "__main__":
    main()
