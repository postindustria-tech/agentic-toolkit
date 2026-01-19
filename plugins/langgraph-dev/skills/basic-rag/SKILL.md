---
name: basic-rag
description: This skill should be used when the user asks about "RAG", "retrieval augmented", "document retrieval", "vector store", "semantic search", "FAISS", "Chroma", "document QA", or needs guidance on implementing RAG patterns with LangGraph.
version: 0.3.1
---

# Basic RAG in LangGraph

RAG (Retrieval-Augmented Generation) grounds LLM responses in retrieved documents, improving factual accuracy and enabling knowledge-base QA.

## RAG Pipeline

**Index Phase**: Load -> Split -> Embed -> Store
**Query Phase**: Embed -> Search -> Retrieve -> Augment -> Generate

## Installation

### Using UV (Recommended)
```bash
uv add langchain-community langchain-core langchain-anthropic
uv add langchain-openai  # For embeddings (Anthropic doesn't provide embeddings)
uv add langchain-text-splitters
uv add faiss-cpu  # or faiss-gpu for CUDA support
uv add langgraph
```

### Using pip
```bash
pip install langchain-community langchain-core langchain-anthropic
pip install langchain-openai langchain-text-splitters
pip install faiss-cpu langgraph
```

**Note**: Anthropic does not provide embedding models. Use OpenAI, Voyage AI, or HuggingFace for embeddings.

## Implementation

```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List

# 1. Load documents
loader: TextLoader = TextLoader("documents.txt")
documents: List[Document] = loader.load()

# 2. Split into chunks
text_splitter: RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
splits: List[Document] = text_splitter.split_documents(documents)

# 3. Create embeddings
embeddings: OpenAIEmbeddings = OpenAIEmbeddings()

# 4. Create vector store
vectorstore: FAISS = FAISS.from_documents(splits, embeddings)

# 5. Create retriever
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# Optional: Save/Load vector store for reuse
vectorstore.save_local("faiss_index")
# To load: vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
```

## RAG in LangGraph Node

```python
import logging
from typing import TypedDict, List
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic

# Configure logging
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# Define state
class RAGState(TypedDict):
    query: str
    documents: List[Document]
    response: str

# Define nodes
def retrieve_node(state: RAGState) -> dict:
    """Retrieve relevant documents from vector store."""
    try:
        docs: List[Document] = vectorstore.similarity_search(state["query"], k=3)
        if not docs:
            logger.warning(f"No documents found for query: {state['query']}")
            return {"documents": [], "response": "No relevant documents found."}
        logger.info(f"Retrieved {len(docs)} documents for query: {state['query']}")
        return {"documents": docs}
    except ConnectionError as e:
        logger.error(f"Vector store connection error: {e}")
        return {"documents": [], "response": "Unable to connect to document store."}
    except ValueError as e:
        logger.error(f"Invalid query format: {e}")
        return {"documents": [], "response": f"Invalid query: {str(e)}"}
    except Exception as e:
        logger.exception(f"Retrieval error for query '{state['query']}': {e}")
        return {"documents": [], "response": f"Retrieval error: {str(e)}"}

def generate_node(state: RAGState) -> dict:
    """Generate response using retrieved documents."""
    if not state["documents"]:
        return {"response": state.get("response", "Unable to retrieve documents.")}

    context: str = "\n\n".join([doc.page_content for doc in state["documents"]])
    prompt: str = f"Context:\n{context}\n\nQuestion: {state['query']}\nAnswer:"

    response = llm.invoke(prompt)
    return {"response": response.content}

# Build the graph
workflow = StateGraph(RAGState)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)

# Define flow (modern pattern using START node)
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

# Compile and execute
app = workflow.compile()

# Example execution
result = app.invoke({
    "query": "What is RAG?",
    "documents": [],
    "response": ""
})
print(result["response"])
```

## State Management Options

### Option 1: TypedDict (Simple)
```python
from typing import TypedDict, List
from langchain_core.documents import Document

class RAGState(TypedDict):
    query: str
    documents: List[Document]
    response: str
```

### Option 2: Pydantic Models (Recommended for Validation)
```python
from pydantic import BaseModel, Field, ConfigDict
from langchain_core.documents import Document

class RAGState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    query: str = Field(description="User query")
    documents: list[Document] = Field(default_factory=list)
    response: str = Field(default="")
```

### Option 3: MessagesState (For Chat Applications)
```python
from langgraph.graph import MessagesState
from langchain_core.documents import Document

class RAGState(MessagesState):
    query: str
    documents: list[Document]
```

## Retrieval Strategies

### Similarity Search (Default)
```python
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)
```

### MMR (Maximum Marginal Relevance) - Diversity
```python
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 3,           # Number of documents to return
        "fetch_k": 10,    # Number to fetch before MMR filtering
        "lambda_mult": 0.5  # Diversity: 0=max diversity, 1=min diversity (default 0.5)
    }
)
```

### Similarity Score Threshold - Quality Filter
```python
retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={
        "score_threshold": 0.5,  # Minimum similarity score (0-1)
        "k": 10  # Maximum documents to return (optional, limits results even above threshold)
    }
)
# Note: If no documents meet the threshold, an empty list is returned.
# The k parameter limits results - only top k documents above threshold are returned.
```

## Graph Execution

### Synchronous
```python
result = app.invoke({"query": "What is RAG?", "documents": [], "response": ""})
```

### Streaming
```python
for chunk in app.stream({"query": "What is RAG?", "documents": [], "response": ""}):
    print(chunk)
```

### Async
```python
result = await app.ainvoke({"query": "What is RAG?", "documents": [], "response": ""})
```

### With Checkpointing (Stateful Conversations)
```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# Run with thread ID for conversation tracking
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke(state, config)
```

## Async Best Practices

Use async nodes for I/O-bound operations (LLM calls, API requests, database queries) to improve throughput with concurrent requests.

### When to Use Async vs Sync

- **Use async** for: LLM API calls, external API requests, database operations, file I/O
- **Use sync** for: CPU-bound operations, simple data transformations, in-memory operations

### Complete Async Node Example

```python
import asyncio
import logging
from typing import TypedDict, List
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic

logger = logging.getLogger(__name__)

# Initialize async-capable LLM
llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

class RAGState(TypedDict):
    query: str
    documents: List[Document]
    response: str

async def async_retrieve_node(state: RAGState) -> dict:
    """Async retrieval for better performance with concurrent requests."""
    try:
        # Use async similarity search if available
        docs: List[Document] = await vectorstore.asimilarity_search(state["query"], k=3)
        if not docs:
            return {"documents": [], "response": "No relevant documents found."}
        return {"documents": docs}
    except Exception as e:
        logger.exception(f"Async retrieval error: {e}")
        return {"documents": [], "response": f"Retrieval error: {str(e)}"}

async def async_generate_node(state: RAGState) -> dict:
    """Async generation for better performance with concurrent requests."""
    if not state["documents"]:
        return {"response": state.get("response", "Unable to retrieve documents.")}
    
    context: str = "\n\n".join([doc.page_content for doc in state["documents"]])
    prompt: str = f"Context:\n{context}\n\nQuestion: {state['query']}\nAnswer:"
    
    # Use async invoke for non-blocking LLM call
    response = await llm.ainvoke(prompt)
    return {"response": response.content}

# Build the async graph
workflow = StateGraph(RAGState)
workflow.add_node("retrieve", async_retrieve_node)
workflow.add_node("generate", async_generate_node)
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()

# Running the async graph
async def process_query(query: str) -> dict:
    """Process a RAG query asynchronously."""
    result = await app.ainvoke({
        "query": query,
        "documents": [],
        "response": ""
    })
    return result

# Execute with asyncio
if __name__ == "__main__":
    result = asyncio.run(process_query("What is RAG?"))
    print(result["response"])

# For multiple concurrent queries
async def process_multiple_queries(queries: List[str]) -> List[dict]:
    """Process multiple queries concurrently."""
    tasks = [process_query(q) for q in queries]
    return await asyncio.gather(*tasks)
```

## Chunking Strategies

**RecursiveCharacterTextSplitter** (recommended):
- `chunk_size=1000`: Characters per chunk
- `chunk_overlap=200`: Overlap to preserve context at boundaries

## Vector Stores

**FAISS**: Fast, in-memory, good for prototyping
**Chroma**: Persistent, production-ready

## Embedding Models

**OpenAI embeddings**: High quality, good for production (requires API key)
**HuggingFace embeddings**: Free, local, various models available
**Voyage AI embeddings**: Optimized for retrieval tasks

### OpenAI Example
```python
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()
```

### HuggingFace Example
```python
# Requires: uv add langchain-huggingface (or pip install langchain-huggingface)
# Note: langchain_community.embeddings.huggingface is deprecated since 0.2.2
from langchain_huggingface import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
```

### Voyage AI Example
```python
# Requires: uv add langchain-voyageai (or pip install langchain-voyageai)
# Note: langchain_community.embeddings.voyageai.VoyageEmbeddings is deprecated
from langchain_voyageai import VoyageAIEmbeddings
embeddings = VoyageAIEmbeddings(model="voyage-3.5")  # or "voyage-3.5-lite" for lower cost
# Legacy models (voyage-3, voyage-3-large) still available but superseded by 3.5 series
```

## Best Practices

1. **Chunk overlap** - Prevents context loss at boundaries
2. **Retrieve k=3-5** - Balance between context and noise
3. **Filter by relevance** - Use similarity scores to filter poor matches
4. **Track sources** - Return source documents for transparency
5. **Error handling** - Handle empty results and retrieval failures gracefully
6. **Persistence** - Save vector stores to avoid reindexing
7. **Checkpointing** - Use checkpointers for stateful conversations

## Advanced Retrieval Techniques

### Parent Document Retriever

Retrieves small chunks for accurate embedding matching, then returns the larger parent document for better context.

```python
from langchain.retrievers.parent_document_retriever import ParentDocumentRetriever
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.storage import InMemoryStore
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Parent splitter creates larger chunks
# Note: add_start_index works correctly with character-based splitting (as used here).
# Known issues exist when using token-based splitting (e.g., from_tiktoken_encoder).
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, add_start_index=True)

# Child splitter creates smaller chunks for embedding
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, add_start_index=True)

# Vector store for child chunks (initialized empty - retriever.add_documents populates it)
vectorstore = FAISS.from_documents([], OpenAIEmbeddings())

# Document store for parent documents
store = InMemoryStore()

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)

# Add documents
retriever.add_documents(documents)

# Retrieve (returns parent documents)
docs = retriever.invoke("What is RAG?")
```

### Multi-Query Retriever

Uses an LLM to generate multiple query variations, improving recall by capturing different phrasings.

```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")

# Create base retriever
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Wrap with multi-query
retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm,
    include_original=True  # Include original query in generated queries
)

# The retriever generates 3 query variations by default
docs = retriever.invoke("What are the benefits of RAG?")
```

## Advanced RAG Patterns (2026 Standards)

### Basic RAG vs. Advanced RAG

**Basic RAG** (this tutorial): Query -> Retrieve -> Generate

**Advanced Patterns**:
- **Adaptive RAG**: Routes to vectorstore OR web search based on query type
- **Corrective RAG (CRAG)**: Grades retrieved docs, rewrites query if docs are poor
- **Self-RAG**: Checks for hallucinations, self-corrects responses
- **Agentic RAG**: Uses tool-calling agents with MessagesState for multi-step retrieval

### When to Use Advanced RAG

Use **Adaptive RAG** when:
- Queries might need current web information
- Knowledge base may not have all answers

Use **Corrective RAG** when:
- Document quality varies
- Retrieval accuracy is critical

Use **Self-RAG** when:
- Factual accuracy is paramount
- Cost of hallucinations is high

## Official LangGraph RAG Tutorials

- **[Adaptive RAG](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/)**: Query routing between vectorstore and web search
- **[Corrective RAG (CRAG)](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/)**: Self-grading documents with query rewriting
- **[Self-RAG](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/)**: Hallucination checking and self-correction
- **[Agentic RAG](https://docs.langchain.com/oss/python/langgraph/agentic-rag)**: Tool-based retrieval agents using MessagesState and LangGraph's tool-calling capabilities

**Note**: LangGraph v1.0.5 is the current stable release (January 2026). The tutorials at langchain-ai.github.io/langgraph have been migrated to docs.langchain.com. Both resources remain valid, but docs.langchain.com contains the most up-to-date patterns and best practices.
