"""
Example 02: Subgraph with Different State Schema

This example demonstrates how to use a subgraph that has a different state schema
from the parent graph. This requires explicit state mapping via a wrapper function.

Use Case: Main workflow processes documents through a specialized document
processor subgraph that has its own state schema.

Key Learning: How to map state between parent and child when schemas differ.
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
import operator


# ============================================================================
# SUBGRAPH: Document Processor (Different Schema)
# ============================================================================

class DocumentState(TypedDict):
    """
    State schema for the document processor subgraph.

    This is completely different from the parent WorkflowState,
    containing only document-specific fields.
    """
    text: str  # Document content
    word_count: int  # Number of words
    processed: bool  # Processing status


def count_words(state: DocumentState) -> dict:
    """Count words in the document text."""
    words = state["text"].split()
    return {"word_count": len(words)}


def mark_processed(state: DocumentState) -> dict:
    """Mark document as processed."""
    return {"processed": True}


def create_document_processor():
    """
    Create the document processor subgraph.

    This subgraph works with DocumentState, which is different
    from the parent's WorkflowState.
    """
    subgraph = StateGraph(DocumentState)

    # Add nodes
    subgraph.add_node("count", count_words)
    subgraph.add_node("mark", mark_processed)

    # Define flow
    subgraph.add_edge(START, "count")
    subgraph.add_edge("count", "mark")
    subgraph.add_edge("mark", END)

    return subgraph.compile()


# ============================================================================
# PARENT GRAPH: Main Workflow (Different Schema)
# ============================================================================

class WorkflowState(TypedDict):
    """
    State schema for the parent workflow.

    This includes multiple document texts and processing results,
    completely different structure from DocumentState.
    """
    documents: Annotated[list[str], operator.add]  # List of document texts
    results: Annotated[list[dict], operator.add]  # Processing results
    total_words: int  # Total word count across all documents


def prepare_documents(state: WorkflowState) -> dict:
    """Initial node that sets up documents."""
    # In a real scenario, this might load from files or database
    # Here we just ensure documents are initialized
    return {}


def create_document_processor_wrapper():
    """
    Create a wrapper function that bridges the state schemas.

    This is the KEY PATTERN for using subgraphs with different schemas:
    1. Extract relevant fields from parent state
    2. Transform to subgraph schema
    3. Invoke subgraph
    4. Transform subgraph output back to parent schema
    """
    # Get the compiled subgraph
    doc_processor = create_document_processor()

    def process_document_batch(state: WorkflowState) -> dict:
        """
        Wrapper function that handles state transformation.

        This function acts as a bridge between WorkflowState and DocumentState.
        """
        results = []
        total_words = 0

        # Process each document through the subgraph
        for doc_text in state["documents"]:
            # STEP 1: Transform parent state → subgraph state
            subgraph_input = {
                "text": doc_text,
                "word_count": 0,
                "processed": False
            }

            # STEP 2: Invoke subgraph with its schema
            subgraph_output = doc_processor.invoke(subgraph_input)

            # STEP 3: Extract results from subgraph output
            word_count = subgraph_output["word_count"]
            total_words += word_count

            # STEP 4: Transform subgraph output → parent state
            results.append({
                "text_preview": doc_text[:50] + "..." if len(doc_text) > 50 else doc_text,
                "word_count": word_count,
                "processed": subgraph_output["processed"]
            })

        # Return parent state updates
        return {
            "results": results,
            "total_words": total_words
        }

    return process_document_batch


def summarize_results(state: WorkflowState) -> dict:
    """Summarize processing results."""
    num_docs = len(state["results"])
    avg_words = state["total_words"] / num_docs if num_docs > 0 else 0

    print(f"\nProcessing Summary:")
    print(f"  Documents processed: {num_docs}")
    print(f"  Total words: {state['total_words']}")
    print(f"  Average words per document: {avg_words:.1f}")

    return {}


def create_main_workflow():
    """
    Create the main workflow that uses the document processor subgraph.

    The subgraph has a different state schema, so we use a wrapper function
    to handle the state transformation.
    """
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("prepare", prepare_documents)

    # Add the wrapper as a node (not the subgraph directly)
    # KEY CONCEPT: When schemas differ, use a wrapper function as the node
    workflow.add_node("process", create_document_processor_wrapper())

    workflow.add_node("summarize", summarize_results)

    # Define flow
    workflow.add_edge(START, "prepare")
    workflow.add_edge("prepare", "process")
    workflow.add_edge("process", "summarize")
    workflow.add_edge("summarize", END)

    return workflow.compile()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run the workflow with example documents."""
    workflow = create_main_workflow()

    print("=" * 70)
    print("Document Processing Workflow")
    print("=" * 70)

    # Example documents
    documents = [
        "This is the first document. It contains several words.",
        "Here is another document with different content and more words to count.",
        "A short doc.",
        "The final document in this batch has quite a bit more text than the others, demonstrating variable document lengths."
    ]

    # Execute workflow
    result = workflow.invoke({
        "documents": documents,
        "results": [],
        "total_words": 0
    })

    # Display results
    print("\nDetailed Results:")
    print("-" * 70)
    for i, doc_result in enumerate(result["results"], 1):
        print(f"\nDocument {i}:")
        print(f"  Preview: {doc_result['text_preview']}")
        print(f"  Words: {doc_result['word_count']}")
        print(f"  Processed: {doc_result['processed']}")

    print("\n" + "=" * 70)
    print("✓ Example completed successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()
