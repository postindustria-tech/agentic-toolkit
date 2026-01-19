---
name: create-workflow
description: Generate a LangGraph StateGraph workflow with nodes, edges, and state schema
argument-hint: workflow_name [--pattern=react|crag|multi-agent|custom]
allowed-tools:
  - Read
  - Write
  - AskUserQuestion
  - Bash
---

# Create LangGraph Workflow

Generate a complete LangGraph workflow with state schema, nodes, edges, and entry points.

## Instructions for Claude

When this command is invoked:

### 1. Gather Requirements

Use `AskUserQuestion` to collect:
- Workflow name (if not provided as argument)
- Pattern to use (if `--pattern` not provided):
  - `react`: ReAct agent with tool calling
  - `crag`: Corrective RAG pipeline
  - `multi-agent`: Multi-agent supervisor
  - `custom`: User defines nodes/edges
- LLM provider preference (or read from settings)
- Whether to include tests (default: yes)

### 2. Read Settings

Read `.claude/langgraph-dev.local.md` if it exists to get:
- `llm_provider` (default: anthropic)
- `llm_model` (default: claude-sonnet-4-5)
- `async_by_default` (default: true)
- `include_type_hints` (default: true)
- `include_docstrings` (default: true)

### 3. Validate Inputs

Check:
- Workflow name is valid Python identifier
- Target directory doesn't already exist
- Pattern is valid (react, crag, multi-agent, custom)

### 4. Generate Directory Structure

Create:
```
{workflow_name}/
├── graph.py        # StateGraph definition
├── state.py        # TypedDict state schema
├── nodes.py        # Node implementations
├── __init__.py
├── requirements.txt
└── README.md
```

If tests requested, also create:
```
{workflow_name}/tests/
├── __init__.py
├── test_state.py
├── test_nodes.py
└── test_graph.py
```

### 5. Generate Code Based on Pattern

#### For ReAct Pattern:
- State with `messages: Annotated[List[BaseMessage], operator.add]`
- Agent node with LLM + tools
- Tool node using ToolNode
- Conditional routing via `should_continue`

#### For CRAG Pattern:
- State with `query`, `documents`, `relevance_scores`, `web_search_needed`
- Retrieve node
- Grade documents node
- Generate node
- Web search node
- Conditional routing based on document quality

#### For Multi-Agent Pattern:
- State with `messages`, `next_agent`
- Supervisor node with structured output routing
- Multiple specialized agent nodes
- Conditional routing to agents

#### For Custom Pattern:
Ask user to specify:
- State fields
- Node names and purposes
- Edge connections

### 6. Generate Files

Use `Write` tool to create all files with:
- Proper imports based on settings
- Type hints (if `include_type_hints=true`)
- Docstrings (if `include_docstrings=true`)
- Async patterns (if `async_by_default=true`)
- LLM configuration matching settings

### 7. Generate requirements.txt

Include:
```
langgraph>=0.2.0
langchain>=0.3.0
langchain-anthropic  # or langchain-groq, langchain-openai
pydantic>=2.0.0
python-dotenv
```

Add pattern-specific requirements:
- ReAct: `langchain-community` for tools
- CRAG: `faiss-cpu`, `langchain-huggingface`
- Multi-Agent: `langchain-core`

### 8. Generate README.md

Include:
- Workflow description
- Installation instructions
- Environment variables needed
- Usage examples
- Pattern-specific notes

### 9. Summary Output

After generation, output:
```
✓ Created workflow: {workflow_name}
✓ Pattern: {pattern}
✓ Files generated: {count}

Next steps:
1. cd {workflow_name}
2. Create .env with API keys
3. pip install -r requirements.txt
4. python -m graph  # or provide run instructions
```

## Pattern Templates

Refer to the following skills for patterns:
- **react-agents** skill: ReAct pattern details
- **corrective-rag** skill: CRAG pattern details
- **multi-agent-supervisor** skill: Multi-agent pattern details

## Example Invocation

```
/langgraph-dev:create-workflow research-assistant --pattern=react
```

Claude should then:
1. Ask about tools to include
2. Read settings or use defaults
3. Generate complete ReAct workflow in `research-assistant/` directory
4. Include tests if requested
5. Provide next steps

## Important Notes

- Always validate before generating (prevent overwrites)
- Use settings file when available
- Generate working, runnable code
- Include clear documentation
- Follow tutorial patterns from skills
