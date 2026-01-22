---
name: corrective-rag-crag
description: This skill should be used when the user asks about "CRAG", "corrective RAG", "document grading", "query rewriting", "RAG quality", "web search fallback", or needs guidance on implementing quality-aware RAG with LangGraph.
version: 0.5.0
---

# Corrective RAG (CRAG)

CRAG improves RAG by grading document relevance and using web search fallback when local retrieval is insufficient.

## CRAG Flow

```
Question --> Retrieve --> Grade Documents -->
  --> If Relevant: Generate
  --> If Not Relevant: Transform Query --> Web Search --> Generate
```

## Implementation Pattern

```python
from typing import Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

# Initialize LLM and tools
# Note: Uses Claude Sonnet 4.5; alternative: use ChatOpenAI for OpenAI models
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", temperature=0)
web_search_tool = TavilySearch(max_results=3)


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: user question
        generation: LLM generation
        web_search: whether to add search ("Yes" or "No")
        documents: list of document contents as strings
    """
    question: str
    generation: str
    web_search: str
    documents: list[str]


class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )


# Create structured output grader
structured_llm_grader = llm.with_structured_output(GradeDocuments)

# System prompt for grading
system = """You are a grader assessing relevance of a retrieved document to a user question.
If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant.
Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

grade_prompt = ChatPromptTemplate.from_messages([
    ("system", system),
    ("human", "Retrieved document: \n\n {document} \n\n User question: {question}"),
])

retrieval_grader = grade_prompt | structured_llm_grader


def retrieve(state: GraphState) -> dict[str, Any]:
    """
    Retrieve documents from vectorstore.
    """
    question = state["question"]
    # Replace with your retriever
    # documents = retriever.invoke(question)
    documents = []  # Placeholder
    return {"documents": documents, "question": question}


def grade_documents(state: GraphState) -> dict[str, Any]:
    """
    Determines whether the retrieved documents are relevant to the question.
    If any document is not relevant or no documents retrieved, triggers web search.
    """
    question = state["question"]
    documents = state["documents"]

    # Handle empty retrieval - trigger web search
    if not documents:
        return {"documents": [], "web_search": "Yes"}

    # Grade each document
    filtered_docs = []
    web_search = "No"

    for doc in documents:
        try:
            score = retrieval_grader.invoke({"question": question, "document": doc})
            if score.binary_score == "yes":
                filtered_docs.append(doc)
            else:
                web_search = "Yes"
        except Exception:
            # On grading failure, trigger web search as fallback
            web_search = "Yes"

    # If all documents filtered out, also trigger web search
    if not filtered_docs:
        web_search = "Yes"

    return {"documents": filtered_docs, "web_search": web_search}


def generate(state: GraphState) -> dict[str, Any]:
    """
    Generate answer using RAG on retrieved documents.
    """
    question = state["question"]
    documents = state["documents"]
    # Replace with your RAG chain
    # generation = rag_chain.invoke({"context": documents, "question": question})
    generation = ""  # Placeholder
    return {"generation": generation}


def transform_query(state: GraphState) -> dict[str, Any]:
    """
    Transform the query to produce a better question for web search.
    """
    question = state["question"]
    better_question = llm.invoke(
        f"Look at the input and try to reason about the underlying semantic intent / meaning. "
        f"Here is the initial question: {question}"
    )
    return {"question": better_question.content}


def web_search(state: GraphState) -> dict[str, Any]:
    """
    Web search based on the re-phrased question using Tavily.
    """
    question = state["question"]
    docs = state["documents"]

    # Web search using Tavily
    try:
        web_results = web_search_tool.invoke({"query": question})
        # Defensive access: verify response is dict and extract results safely
        if isinstance(web_results, dict):
            results_list = web_results.get("results", [])
            if isinstance(results_list, list):
                web_content = "\n".join([
                    d.get("content", "") for d in results_list
                    if isinstance(d, dict)
                ])
            else:
                web_content = ""
        else:
            web_content = ""
    except Exception:
        web_content = ""

    if web_content:
        docs = docs + [web_content]

    return {"documents": docs}


def decide_to_generate(state: GraphState) -> str:
    """
    Determines whether to generate an answer, or re-generate a question.
    """
    if state["web_search"] == "Yes":
        return "transform_query"
    return "generate"


# Build graph
workflow = StateGraph(GraphState)

# Define the nodes
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)
workflow.add_node("web_search_node", web_search)

# Build graph edges
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)
workflow.add_edge("transform_query", "web_search_node")
workflow.add_edge("web_search_node", "generate")
workflow.add_edge("generate", END)

# Compile
app = workflow.compile()

# Example usage
initial_state = {
    "question": "What is the capital of France?",
    "generation": "",
    "web_search": "No",
    "documents": []
}
result = app.invoke(initial_state)
print(result["generation"])
```

## When to Use CRAG

- Document quality varies
- Local knowledge may be incomplete
- Need web search as backup
- Quality-aware generation important

## Advanced: Knowledge Refinement

The original CRAG paper includes a knowledge refinement step that decomposes documents into "knowledge strips" and filters them individually. This implementation simplifies by filtering whole documents. For the full paper approach, see the [CRAG paper (arXiv:2401.15884)](https://arxiv.org/abs/2401.15884).

## Benefits

1. **Quality filtering** - Only use relevant documents
2. **Adaptive retrieval** - Fallback to web when needed
3. **Query optimization** - Rewrite for better results
4. **Transparency** - Know when web search used

## Related Patterns

- **Self-RAG**: Adds self-reflection on generations, not just retrieval. [Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/)
- **Adaptive RAG**: Combines query analysis with active/self-corrective RAG. [Tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/)

## References

- **Official Tutorial**: [Corrective RAG (CRAG)](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/)
- **Local LLMs Version**: [CRAG with Local LLMs](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag_local/)
- **Research Paper**: [CRAG: Corrective Retrieval Augmented Generation (arXiv:2401.15884)](https://arxiv.org/abs/2401.15884)
