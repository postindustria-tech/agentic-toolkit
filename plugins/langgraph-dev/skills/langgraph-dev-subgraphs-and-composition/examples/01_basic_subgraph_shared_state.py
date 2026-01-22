"""
Example 01: Basic Subgraph with Shared State

This example demonstrates the simplest form of subgraph composition where both
parent and child graphs share the same state schema (MessagesState).

Use Case: Chatbot with sentiment analysis subgraph that analyzes user input
before generating a response.

Key Learning: How to add a compiled graph as a node directly when schemas match.
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


# ============================================================================
# SUBGRAPH: Sentiment Analyzer
# ============================================================================

def analyze_sentiment(state: MessagesState) -> MessagesState:
    """
    Analyze the sentiment of the last message.

    In a real implementation, this would call an LLM or sentiment API.
    Here we use simple keyword matching for demonstration.
    """
    last_message = state["messages"][-1].content.lower()

    # Simple sentiment detection
    positive_words = ["happy", "great", "excellent", "love", "wonderful"]
    negative_words = ["sad", "bad", "terrible", "hate", "awful"]

    positive_count = sum(1 for word in positive_words if word in last_message)
    negative_count = sum(1 for word in negative_words if word in last_message)

    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Add sentiment analysis result as a system message
    analysis_message = SystemMessage(
        content=f"[Sentiment Analysis: {sentiment}]"
    )

    return {"messages": [analysis_message]}


def create_sentiment_subgraph():
    """
    Create the sentiment analysis subgraph.

    This is a simple linear graph with just one node, but demonstrates
    the fundamental pattern of creating a reusable subgraph component.
    """
    subgraph = StateGraph(MessagesState)
    subgraph.add_node("analyze", analyze_sentiment)
    subgraph.add_edge(START, "analyze")
    subgraph.add_edge("analyze", END)

    # Compile and return - this compiled graph can be used as a node
    return subgraph.compile()


# ============================================================================
# PARENT GRAPH: Chatbot
# ============================================================================

def generate_response(state: MessagesState) -> MessagesState:
    """
    Generate a response based on the conversation and sentiment analysis.

    In a real implementation, this would call an LLM.
    Here we generate simple responses based on the sentiment.
    """
    # Extract sentiment from the last system message (added by subgraph)
    sentiment_msg = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, SystemMessage) and "Sentiment Analysis:" in msg.content:
            sentiment_msg = msg.content
            break

    # Generate response based on sentiment
    if sentiment_msg and "positive" in sentiment_msg:
        response = "I'm glad you're feeling positive! How can I help you today?"
    elif sentiment_msg and "negative" in sentiment_msg:
        response = "I'm sorry you're feeling that way. I'm here to help."
    else:
        response = "Thank you for your message. How can I assist you?"

    return {"messages": [AIMessage(content=response)]}


def create_chatbot():
    """
    Create the main chatbot graph that uses the sentiment subgraph.

    This demonstrates adding a compiled graph as a node.
    """
    # Create the sentiment subgraph (compiled graph)
    sentiment_subgraph = create_sentiment_subgraph()

    # Create parent graph
    chatbot = StateGraph(MessagesState)

    # Add the compiled subgraph as a regular node
    # KEY CONCEPT: sentiment_subgraph is callable, so it can be a node
    chatbot.add_node("sentiment", sentiment_subgraph)

    # Add response generation node
    chatbot.add_node("respond", generate_response)

    # Define flow: START → sentiment analysis → response → END
    chatbot.add_edge(START, "sentiment")
    chatbot.add_edge("sentiment", "respond")
    chatbot.add_edge("respond", END)

    return chatbot.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run the chatbot with example inputs."""
    chatbot = create_chatbot()

    # Example 1: Positive sentiment
    print("=" * 70)
    print("Example 1: Positive Message")
    print("=" * 70)

    result1 = chatbot.invoke({
        "messages": [HumanMessage(content="I'm having a wonderful day!")]
    })

    for msg in result1["messages"]:
        print(f"{msg.__class__.__name__}: {msg.content}")

    # Example 2: Negative sentiment
    print("\n" + "=" * 70)
    print("Example 2: Negative Message")
    print("=" * 70)

    result2 = chatbot.invoke({
        "messages": [HumanMessage(content="This is terrible and I hate it.")]
    })

    for msg in result2["messages"]:
        print(f"{msg.__class__.__name__}: {msg.content}")

    # Example 3: Neutral sentiment
    print("\n" + "=" * 70)
    print("Example 3: Neutral Message")
    print("=" * 70)

    result3 = chatbot.invoke({
        "messages": [HumanMessage(content="What's the weather like?")]
    })

    for msg in result3["messages"]:
        print(f"{msg.__class__.__name__}: {msg.content}")

    print("\n" + "=" * 70)
    print("✓ Example completed successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()
