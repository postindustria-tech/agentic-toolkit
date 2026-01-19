# LangGraph Development Plugin

**Version**: 0.1.0

**Status**: Skills are tested and ready to use. Commands and agent are work in progress.

Tutorial and docs-grounded patterns and best practices for building agentic systems with LangGraph and LangChain.

## What's Included

### 22 Skills

**Core LangGraph Fundamentals:**
- `state-management` - TypedDict schemas, Annotated fields, state patterns
- `graph-construction` - Nodes, edges, compilation, visualization
- `conditional-routing` - Branching logic, dynamic routing
- `streaming-execution` - Event streaming, monitoring

**Agent & Tool Patterns:**
- `tool-calling` - ToolNode integration, model.bind_tools()
- `react-agents` - ReAct pattern, reasoning loops
- `multi-agent-supervisor` - Agent coordination, orchestration
- `parallel-execution` - Fan-out/fan-in, parallel nodes

**RAG & Document Processing:**
- `basic-rag` - Document retrieval, vector stores
- `corrective-rag` - CRAG pattern, quality grading
- `document-processing` - Text splitting, chunking strategies

**Memory & Context:**
- `conversation-memory` - Buffer, summary, knowledge graph memory

**Structured Data:**
- `structured-output` - Pydantic models, output parsing

**Error Handling:**
- `error-recovery` - Fallbacks, retry strategies

**Testing & Production:**
- `testing-agentic-systems` - Mocking, evaluation metrics
- `deployment-patterns` - FastAPI integration
- `performance-optimization` - Caching, cost tracking

**Advanced Techniques:**
- `prompt-engineering` - Template patterns, few-shot learning

### 5 Commands (WIP)

Code generators for scaffolding:

- `/langgraph-dev:create-workflow` - Generate StateGraph with nodes/edges
- `/langgraph-dev:create-state` - Generate TypedDict state schema
- `/langgraph-dev:create-tests` - Generate test suite
- `/langgraph-dev:create-agent` - Generate ReAct agent
- `/langgraph-dev:create-deployment` - Generate FastAPI deployment

### 1 Agent (WIP)

- `workflow-validator` - Graph structure validation

## Installation

Install from the agentic-toolkit marketplace:

```bash
/plugin marketplace add postindustria-tech/agentic-toolkit
/plugin install langgraph-dev@agentic-toolkit
```

## Usage

Skills activate automatically when you ask LangGraph-related questions:

```
"How do I create a LangGraph state schema with reducers?"
→ state-management skill provides patterns

"Show me the ReAct agent pattern"
→ react-agents skill provides implementation guidance

"How do I implement CRAG?"
→ corrective-rag skill explains the pattern
```

## Configuration

Optional: Create `.claude/langgraph-dev.local.md` for custom settings. See `examples/langgraph-dev.local.md.example`.

## Sources

Skills are based on tutorials from [langchain-langgraph-starter](https://github.com/rahulsamant37/langchain-langgraph-starter) and official LangGraph documentation.

## Skills Reference

Each skill includes:
- Core patterns and concepts
- Reference documentation for advanced topics
- Working code examples

## Resources

- Tutorial repository: https://github.com/rahulsamant37/langchain-langgraph-starter
- LangGraph docs: https://langchain-ai.github.io/langgraph/

## License

MIT License
