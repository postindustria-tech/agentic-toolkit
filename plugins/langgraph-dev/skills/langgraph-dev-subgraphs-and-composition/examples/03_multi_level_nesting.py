"""
Example 03: Multi-Level Nesting

This example demonstrates three-level hierarchy (parent → child → grandchild)
with state propagation through all levels.

Use Case: Research assistant where the Topic Analyzer (child) uses a
Keyword Extractor (grandchild) as part of its analysis workflow.

Key Learning: How state flows through multiple levels of composition.
"""

from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


# ============================================================================
# GRANDCHILD GRAPH: Keyword Extractor
# ============================================================================

def extract_keywords(state: MessagesState) -> dict:
    """
    Extract keywords from the last message (Level 3 - deepest).

    In a real implementation, this might use NLP or an LLM.
    Here we use simple heuristics.
    """
    last_message = state["messages"][-1].content.lower()

    # Simple keyword extraction (words longer than 5 characters)
    words = last_message.split()
    keywords = [word for word in words if len(word) > 5]

    # Take top 3 most interesting keywords
    keywords = keywords[:3]

    keyword_message = SystemMessage(
        content=f"[Keywords: {', '.join(keywords)}]"
    )

    print("    → Grandchild (Keyword Extractor): Extracted keywords")

    return {"messages": [keyword_message]}


def create_keyword_extractor():
    """
    Create the keyword extractor subgraph (Level 3 - grandchild).
    """
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("extract", extract_keywords)
    subgraph.add_edge(START, "extract")
    subgraph.add_edge("extract", END)

    print("  Creating Grandchild Graph (Keyword Extractor)")
    return subgraph.compile()


# ============================================================================
# CHILD GRAPH: Topic Analyzer
# ============================================================================

def identify_topic(state: MessagesState) -> dict:
    """
    Identify the topic of the research query (Level 2).

    This node runs before the keyword extractor.
    """
    last_message = state["messages"][-1].content.lower()

    # Simple topic identification
    if "machine learning" in last_message or "ai" in last_message:
        topic = "Artificial Intelligence"
    elif "climate" in last_message or "environment" in last_message:
        topic = "Environmental Science"
    elif "quantum" in last_message or "physics" in last_message:
        topic = "Physics"
    else:
        topic = "General Research"

    topic_message = SystemMessage(
        content=f"[Topic: {topic}]"
    )

    print(f"  → Child (Topic Analyzer): Identified topic as '{topic}'")

    return {"messages": [topic_message]}


def synthesize_analysis(state: MessagesState) -> dict:
    """
    Synthesize the final analysis combining topic and keywords (Level 2).

    This node runs after the keyword extractor (grandchild).
    """
    # Extract topic and keywords from system messages
    topic = "Unknown"
    keywords = "None"

    for msg in state["messages"]:
        if isinstance(msg, SystemMessage):
            if "[Topic:" in msg.content:
                topic = msg.content.split("[Topic:")[1].split("]")[0].strip()
            elif "[Keywords:" in msg.content:
                keywords = msg.content.split("[Keywords:")[1].split("]")[0].strip()

    synthesis_message = SystemMessage(
        content=f"[Analysis: Topic={topic}, Keywords={keywords}]"
    )

    print(f"  → Child (Topic Analyzer): Synthesized analysis")

    return {"messages": [synthesis_message]}


def create_topic_analyzer():
    """
    Create the topic analyzer subgraph (Level 2 - child).

    This subgraph contains the keyword extractor as a nested subgraph.
    """
    # Create the grandchild graph first
    keyword_extractor = create_keyword_extractor()

    # Create child graph
    subgraph = StateGraph(MessagesState)

    # Add nodes
    subgraph.add_node("identify", identify_topic)
    subgraph.add_node("extract_keywords", keyword_extractor)  # Nested subgraph!
    subgraph.add_node("synthesize", synthesize_analysis)

    # Define flow: identify → extract keywords (grandchild) → synthesize
    subgraph.add_edge(START, "identify")
    subgraph.add_edge("identify", "extract_keywords")
    subgraph.add_edge("extract_keywords", "synthesize")
    subgraph.add_edge("synthesize", END)

    print("Creating Child Graph (Topic Analyzer)")
    return subgraph.compile()


# ============================================================================
# PARENT GRAPH: Research Coordinator
# ============================================================================

def receive_query(state: MessagesState) -> dict:
    """
    Initial node that receives the research query (Level 1).
    """
    print("→ Parent (Research Coordinator): Received query")
    return {}


def generate_research_plan(state: MessagesState) -> dict:
    """
    Generate a research plan based on the analysis (Level 1).

    This runs after the topic analyzer (child) completes.
    """
    # Extract analysis from system messages
    analysis = "No analysis available"
    for msg in reversed(state["messages"]):
        if isinstance(msg, SystemMessage) and "[Analysis:" in msg.content:
            analysis = msg.content.split("[Analysis:")[1].split("]")[0].strip()
            break

    plan = f"Research Plan based on {analysis}: " \
           "1) Literature review, 2) Data collection, 3) Analysis"

    plan_message = AIMessage(content=plan)

    print(f"→ Parent (Research Coordinator): Generated research plan")

    return {"messages": [plan_message]}


def create_research_coordinator():
    """
    Create the research coordinator (Level 1 - parent).

    This is the top-level graph that orchestrates the research workflow.
    """
    # Create the child graph (which contains the grandchild)
    topic_analyzer = create_topic_analyzer()

    # Create parent graph
    workflow = StateGraph(MessagesState)

    # Add nodes
    workflow.add_node("receive", receive_query)
    workflow.add_node("analyze", topic_analyzer)  # Nested child graph!
    workflow.add_node("plan", generate_research_plan)

    # Define flow
    workflow.add_edge(START, "receive")
    workflow.add_edge("receive", "analyze")
    workflow.add_edge("analyze", "plan")
    workflow.add_edge("plan", END)

    print("Creating Parent Graph (Research Coordinator)")
    return workflow.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run the research coordinator with example queries."""

    # Example 1: AI research query
    print("=" * 70)
    print("Example 1: AI Research Query")
    print("=" * 70)
    print()

    coordinator = create_research_coordinator()
    print()

    result1 = coordinator.invoke({
        "messages": [HumanMessage(
            content="I want to research machine learning applications in healthcare"
        )]
    })

    print("\n--- Final State Messages ---")
    for i, msg in enumerate(result1["messages"], 1):
        print(f"{i}. {msg.__class__.__name__}: {msg.content}")

    # Example 2: Climate research query
    print("\n\n" + "=" * 70)
    print("Example 2: Climate Research Query")
    print("=" * 70)
    print()

    result2 = coordinator.invoke({
        "messages": [HumanMessage(
            content="Investigating climate change impact on coastal environments"
        )]
    })

    print("\n--- Final State Messages ---")
    for i, msg in enumerate(result2["messages"], 1):
        print(f"{i}. {msg.__class__.__name__}: {msg.content}")

    print("\n" + "=" * 70)
    print("✓ Example completed successfully")
    print("=" * 70)
    print("\nKey Observation:")
    print("  State flowed through 3 levels: Parent → Child → Grandchild")
    print("  Each level added its own system messages to the shared state")
    print("  Parent used the analysis from child (which used grandchild output)")


if __name__ == "__main__":
    main()
