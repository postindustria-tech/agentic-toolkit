---
name: document-processing-for-rag
description: This skill should be used when the user asks about "load documents", "text splitting", "chunking strategy", "document loader", "PDF processing", "RecursiveCharacterTextSplitter", or needs guidance on processing documents for RAG systems.
version: 0.2.3
---

# Document Processing for RAG

Document processing transforms raw files into chunked, searchable documents for RAG pipelines.

## Installation

```bash
pip install langchain-community langchain-text-splitters langchain-huggingface faiss-cpu
# Or for GPU support:
pip install faiss-gpu

# For hybrid search (BM25 + semantic):
pip install rank-bm25
```

## Processing Pipeline (Tutorial 03)

**Load -> Split -> Embed -> Index**

## Document Loaders

```python
from langchain_community.document_loaders import (
    TextLoader,
    DirectoryLoader,
    PyPDFLoader
)

# Single text file
loader = TextLoader("document.txt")
docs = loader.load()

# Directory of files
# loader_cls defaults to UnstructuredFileLoader (requires 'unstructured' package)
# TextLoader is simpler and works for plain text files
loader = DirectoryLoader("docs/", glob="*.txt", loader_cls=TextLoader)
docs = loader.load()

# PDF files (requires: pip install pypdf)
loader = PyPDFLoader("document.pdf")
pages = loader.load()
```

## Text Splitters

### RecursiveCharacterTextSplitter (Recommended)

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # Characters per chunk (default: 4000)
    chunk_overlap=200,    # Overlap between chunks (default: 200)
    length_function=len   # Default length function
)

chunks = splitter.split_documents(documents)  # 'documents' from loader.load()
```

**Why overlap?** Prevents context loss at chunk boundaries.

### CharacterTextSplitter (Simple)

```python
from langchain_text_splitters import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=0,
    separator="\n\n"  # Split on paragraphs (default)
)

# Usage
chunks = splitter.split_documents(documents)
# Or for raw text:
# text_chunks = splitter.split_text(text)
```

## Chunking Best Practices

**Chunk Size Guidelines** (in characters with `length_function=len`):
- Small (200-500): Precise retrieval, may lack context
- Medium (500-1000): **Recommended** - Balance of precision and context
- Large (1000-2000): More context, less precise

**Note**: When using token-based chunking (e.g., tiktoken), divide these values by ~4 for approximate token counts.

**Overlap Guidelines**:
- 10-20% of chunk_size is typical
- 200 chars for 1000-char chunks
- Prevents splitting mid-sentence

## Metadata Preservation

```python
# Documents retain source metadata after splitting
for doc in chunks:
    print(doc.metadata)
    # TextLoader: {'source': 'file.txt'}
    # PyPDFLoader: {'source': 'document.pdf', 'page': 0}
```

## Processing Workflow

```python
from typing import List
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def process_documents(directory_path: str, glob_pattern: str = "*.txt") -> FAISS:
    """Complete document processing pipeline."""
    # 1. Load
    loader = DirectoryLoader(directory_path, glob=glob_pattern)
    documents = loader.load()

    # 2. Split
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(documents)

    # 3. Embed
    embeddings = HuggingFaceEmbeddings()

    # 4. Index
    vectorstore = FAISS.from_documents(chunks, embeddings)

    return vectorstore
```

## Common Patterns

**Filter by metadata**:
```python
retriever = vectorstore.as_retriever(
    search_kwargs={"filter": {"source": "important.txt"}}
)
```

**Hybrid search** (keyword + semantic):
```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# Create retrievers
# Note: k parameter is passed via **kwargs to set number of documents to return (default: 4)
bm25_retriever = BM25Retriever.from_documents(documents, k=3)
semantic_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Create ensemble with weights
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, semantic_retriever],
    weights=[0.5, 0.5]
)
```

## Tutorial Reference

**Tutorial 03**: Document Processing with LangChain - Complete loading and chunking patterns
